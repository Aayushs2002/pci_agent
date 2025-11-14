"""
PCI Compliance Agent - File Scanner
Handles file system traversal and content scanning
"""

import os
import logging
import mimetypes
import chardet
from pathlib import Path
from typing import List, Generator, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import fnmatch
import magic
from tqdm import tqdm

from detection_engine import PANDetector, PANMatch

logger = logging.getLogger(__name__)

class FileScanner:
    """Handles secure file system scanning with configurable exclusions"""
    
    def __init__(self, config: dict, detector: PANDetector):
        self.config = config
        self.detector = detector
        self.agent_config = config.get('agent', {})
        
        # Scanning limits
        self.max_files = self.agent_config.get('max_files_per_scan', 10000)
        self.max_depth = self.agent_config.get('max_recursion_depth', 8)
        self.concurrency = self.agent_config.get('concurrency', 4)
        self.batch_size = self.agent_config.get('batch_size', 1000)
        
        # Unlimited if set to 0
        if self.max_files == 0:
            self.max_files = float('inf')
        if self.max_depth == 0:
            self.max_depth = float('inf')
        
        # File type settings
        self.scan_text_files = self.agent_config.get('scan_text_files', True)
        self.scan_binary_files = self.agent_config.get('scan_binary_files', False)
        
        # Exclusion patterns
        self.exclude_patterns = set(self.agent_config.get('exclude_patterns', []))
        
        # Statistics
        self.stats = {
            'files_scanned': 0,
            'files_skipped': 0,
            'directories_scanned': 0,
            'matches_found': 0,
            'errors': 0
        }
        
        # Control flags
        self.stop_requested = False
        
        logger.info(f"FileScanner initialized: max_files={'unlimited' if self.max_files == float('inf') else self.max_files}, "
                   f"max_depth={'unlimited' if self.max_depth == float('inf') else self.max_depth}, "
                   f"concurrency={self.concurrency}, batch_size={self.batch_size}")
    
    def is_excluded(self, path: str) -> bool:
        """Check if path matches any exclusion pattern"""
        path_str = str(path).replace('\\', '/')  # Normalize path separators
        
        for pattern in self.exclude_patterns:
            # Convert Windows-style patterns to Unix-style for consistency
            pattern = pattern.replace('\\', '/')
            
            if fnmatch.fnmatch(path_str, pattern):
                logger.debug(f"Excluding {path_str} (matches pattern: {pattern})")
                return True
                
            # Also check if any parent directory matches
            if fnmatch.fnmatch(os.path.dirname(path_str), pattern.rstrip('/*')):
                logger.debug(f"Excluding {path_str} (parent matches pattern: {pattern})")
                return True
        
        return False
    
    def detect_file_type(self, file_path: str) -> tuple[str, str]:
        """
        Detect file type and encoding
        Returns (mime_type, encoding)
        """
        try:
            # Try python-magic first for better accuracy
            if hasattr(magic, 'from_file'):
                mime_type = magic.from_file(file_path, mime=True)
            else:
                # Fallback to mimetypes
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = 'application/octet-stream'
            
            # Detect encoding for text files
            encoding = 'utf-8'  # Default
            if mime_type and mime_type.startswith('text/'):
                try:
                    with open(file_path, 'rb') as f:
                        raw_data = f.read(8192)  # Read first 8KB for detection
                        detected = chardet.detect(raw_data)
                        if detected and detected['encoding']:
                            encoding = detected['encoding']
                except Exception as e:
                    logger.debug(f"Encoding detection failed for {file_path}: {e}")
            
            return mime_type, encoding
            
        except Exception as e:
            logger.debug(f"File type detection failed for {file_path}: {e}")
            return 'application/octet-stream', 'utf-8'
    
    def should_scan_file(self, file_path: str) -> bool:
        """Determine if file should be scanned based on type and configuration"""
        try:
            # Basic validation
            if not self.detector.validate_file_for_scanning(file_path):
                return False
            
            # Check exclusion patterns
            if self.is_excluded(file_path):
                return False
            
            # Detect file type
            mime_type, _ = self.detect_file_type(file_path)
            
            # Text files
            if mime_type.startswith('text/'):
                return self.scan_text_files
            
            # Application files that might contain text
            text_like_apps = [
                'application/json',
                'application/xml',
                'application/javascript',
                'application/sql',
                'application/yaml'
            ]
            
            if mime_type in text_like_apps:
                return self.scan_text_files
            
            # Binary files
            return self.scan_binary_files
            
        except Exception as e:
            logger.warning(f"Error checking if should scan {file_path}: {e}")
            return False
    
    def read_file_content(self, file_path: str) -> Optional[str]:
        """
        Safely read file content with encoding detection
        Returns None if file cannot be read as text
        """
        try:
            mime_type, encoding = self.detect_file_type(file_path)
            
            # For binary files, only attempt if specifically configured
            if not mime_type.startswith('text/') and not self.scan_binary_files:
                # Check if it's a text-like application file
                text_like_apps = [
                    'application/json', 'application/xml', 'application/javascript',
                    'application/sql', 'application/yaml'
                ]
                if mime_type not in text_like_apps:
                    return None
            
            # Attempt to read with detected encoding
            encodings_to_try = [encoding, 'utf-8', 'latin1', 'cp1252']
            
            for enc in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                        content = f.read()
                        if content:  # Successfully read non-empty content
                            logger.debug(f"Read {file_path} with encoding {enc}")
                            return content
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.debug(f"Failed to read {file_path} with {enc}: {e}")
                    continue
            
            logger.debug(f"Could not read {file_path} with any encoding")
            return None
            
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            self.stats['errors'] += 1
            return None
    
    def scan_file(self, file_path: str) -> List[PANMatch]:
        """
        Scan a single file for PAN matches
        Returns list of matches found
        """
        try:
            if not self.should_scan_file(file_path):
                self.stats['files_skipped'] += 1
                return []
            
            content = self.read_file_content(file_path)
            if content is None:
                self.stats['files_skipped'] += 1
                return []
            
            matches = self.detector.scan_text(content, file_path)
            
            self.stats['files_scanned'] += 1
            self.stats['matches_found'] += len(matches)
            
            if matches:
                logger.info(f"Found {len(matches)} potential PANs in {file_path}")
            
            return matches
            
        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
            self.stats['errors'] += 1
            return []
    
    def walk_directory(self, directory: str, current_depth: int = 0) -> Generator[str, None, None]:
        """
        Generator that yields file paths while respecting depth and exclusion limits
        """
        if self.max_depth != float('inf') and current_depth > self.max_depth:
            logger.debug(f"Max depth reached at {directory}")
            return
        
        try:
            directory_path = Path(directory)
            if not directory_path.exists() or not directory_path.is_dir():
                logger.warning(f"Directory does not exist or is not accessible: {directory}")
                return
            
            if self.is_excluded(str(directory_path)):
                logger.debug(f"Directory excluded: {directory}")
                return
            
            self.stats['directories_scanned'] += 1
            
            for item in directory_path.iterdir():
                # Check global file count limit (across all directories)
                if self.stats['files_scanned'] >= self.max_files:
                    logger.warning(f"Global max files limit ({self.max_files}) reached")
                    return
                
                try:
                    if item.is_file():
                        if not self.is_excluded(str(item)):
                            yield str(item)
                    elif item.is_dir():
                        # Recursively walk subdirectories
                        yield from self.walk_directory(str(item), current_depth + 1)
                        
                except (PermissionError, OSError) as e:
                    # Skip files/folders with access denied - this is normal for system folders
                    logger.debug(f"Access denied (skipping): {item}")
                    self.stats['files_skipped'] += 1
                    continue
                    
        except PermissionError as e:
            # Permission denied on directory - skip silently (common for system folders)
            logger.debug(f"Access denied (skipping directory): {directory}")
            self.stats['errors'] += 1
        except Exception as e:
            # Other errors - log as warning
            logger.warning(f"Error accessing directory {directory}: {e}")
            self.stats['errors'] += 1
    
    def request_stop(self):
        """Request the scan to stop gracefully"""
        logger.info("Stop requested - scan will terminate after current files complete")
        self.stop_requested = True
    
    def scan_directories(self, directories: List[str], progress_callback=None) -> List[PANMatch]:
        """
        Scan multiple directories for PAN matches with concurrent processing
        Two-pass approach: 1) Count files, 2) Scan with accurate progress
        """
        # Reset stop flag at start of scan
        self.stop_requested = False
        
        logger.info(f"Starting scan of {len(directories)} directories")
        
        # PASS 1: Count total files first (fast - just walking directories)
        logger.info("Counting files...")
        if progress_callback:
            progress_callback({
                'phase': 'counting',
                'message': 'Counting files...',
                'files_scanned': 0,
                'total_files': 0,
                'matches_found': 0
            })
        
        all_files = []
        for directory in directories:
            logger.info(f"Counting files in: {directory}")
            for file_path in self.walk_directory(directory):
                all_files.append(file_path)
                
                # Update count progress every 1000 files
                if len(all_files) % 1000 == 0:
                    logger.info(f"Found {len(all_files)} files so far...")
                    if progress_callback:
                        progress_callback({
                            'phase': 'counting',
                            'message': f'Found {len(all_files)} files...',
                            'files_scanned': 0,
                            'total_files': len(all_files),
                            'matches_found': 0
                        })
                
                # Check for stop during counting
                if self.stop_requested:
                    logger.info("Stop requested during file counting")
                    return []
                
                # Respect max_files limit
                if len(all_files) >= self.max_files:
                    logger.warning(f"Reached maximum file limit during counting: {int(self.max_files)}")
                    break
        
        total_files = len(all_files)
        logger.info(f"Found {total_files} files to scan")
        
        if total_files == 0:
            logger.warning("No files found to scan")
            return []
        
        # PASS 2: Scan files with accurate progress
        logger.info(f"Starting scan of {total_files} files...")
        if progress_callback:
            progress_callback({
                'phase': 'scanning',
                'message': 'Scanning files...',
                'files_scanned': 0,
                'total_files': total_files,
                'matches_found': 0
            })
        
        all_matches = []
        files_completed = 0
        
        # Scan files using thread pool with accurate progress
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = {}
            file_index = 0
            
            # Submit initial batch to fill the thread pool
            initial_batch_size = min(self.concurrency * 2, total_files)
            for i in range(initial_batch_size):
                if file_index < total_files:
                    file_path = all_files[file_index]
                    future = executor.submit(self.scan_file, file_path)
                    futures[future] = file_path
                    file_index += 1
            
            # Process results as they complete
            while futures:
                # Check if stop was requested
                if self.stop_requested:
                    logger.info("Stop requested - cancelling remaining futures")
                    for future in futures.keys():
                        future.cancel()
                    break
                
                # Wait for at least one future to complete
                for future in as_completed(futures.keys()):
                    file_path = futures.pop(future)
                    
                    try:
                        matches = future.result()
                        if matches:
                            all_matches.extend(matches)
                        
                        files_completed += 1
                        
                        # Log progress every 1000 files
                        if files_completed % 1000 == 0:
                            percentage = (files_completed / total_files) * 100
                            logger.info(f"Progress: {files_completed}/{total_files} files ({percentage:.1f}%), "
                                      f"{len(all_matches)} matches found")
                        
                        # Send progress update to GUI
                        if progress_callback:
                            progress_callback({
                                'phase': 'scanning',
                                'files_scanned': files_completed,
                                'total_files': total_files,
                                'matches_found': len(all_matches),
                                'current_file': file_path,
                                'in_queue': len(futures),
                                'percentage': round((files_completed / total_files) * 100, 1)
                            })
                    
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        self.stats['errors'] += 1
                        files_completed += 1
                    
                    # Submit new file to replace completed one (keep pipeline full)
                    if file_index < total_files and not self.stop_requested:
                        next_file = all_files[file_index]
                        new_future = executor.submit(self.scan_file, next_file)
                        futures[new_future] = next_file
                        file_index += 1
                    
                    break  # Process one at a time
        
        # Send final progress update
        if progress_callback:
            progress_callback({
                'phase': 'complete',
                'files_scanned': files_completed,
                'total_files': total_files,
                'matches_found': len(all_matches),
                'current_file': 'Scan complete',
                'in_queue': 0,
                'percentage': 100,
                'completed': True
            })
        
        status = "stopped" if self.stop_requested else "completed"
        logger.info(f"Scan {status}: {files_completed}/{total_files} files scanned, "
                   f"{len(all_matches)} matches found, {self.stats['errors']} errors")
        
        return all_matches
    
    def get_stats(self) -> dict:
        """Return scanning statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset scanning statistics"""
        for key in self.stats:
            self.stats[key] = 0