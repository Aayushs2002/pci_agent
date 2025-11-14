const request = require('supertest');
const app = require('../server');
const { getDatabase } = require('../database/connection');

describe('Server Health Endpoints', () => {
  test('GET /api/health should return health status', async () => {
    const response = await request(app)
      .get('/api/health')
      .expect(200);
    
    expect(response.body).toHaveProperty('status', 'healthy');
    expect(response.body).toHaveProperty('version');
    expect(response.body).toHaveProperty('uptime');
  });
});

describe('Reports API', () => {
  const validReport = {
    metadata: {
      report_version: '1.0',
      agent_id: 'test-agent-001',
      scan_id: 'test-scan-001',
      timestamp: new Date().toISOString(),
      operator: 'test-operator',
      report_hash: 'test-hash-123'
    },
    scan_parameters: {
      directories_scanned: 2,
      exclude_patterns_count: 5,
      detect_plain_pan_enabled: false,
      action_policy: 'report_only',
      max_file_size_mb: 10,
      concurrency: 4,
      privacy_settings: {
        redact_pan: true,
        show_last4_only: true
      }
    },
    scan_results: {
      summary: {
        total_files_scanned: 100,
        total_files_skipped: 10,
        total_directories_scanned: 2,
        total_matches_found: 1,
        errors_encountered: 0
      },
      findings_by_type: {
        by_card_type: { visa: 1 },
        by_validation_status: { luhn_valid: 1, luhn_invalid: 0 }
      },
      findings: [
        {
          file_path: '/test/path/file.txt',
          line_number: 1,
          column_range: [10, 26],
          card_type: 'visa',
          luhn_valid: true,
          confidence_score: 0.95,
          is_masked: false,
          context: {
            before: 'Card: ',
            after: ' expires'
          },
          remediation_priority: 'high',
          remediation_suggestions: ['Mask PAN immediately'],
          pan_data: {
            masked_number: '****1234',
            hash: 'abc123def456'
          }
        }
      ],
      risk_assessment: {
        overall_risk: 'high',
        risk_factors: ['Unmasked PAN detected'],
        compliance_status: 'non-compliant'
      }
    },
    compliance_notes: {
      data_handling: 'PCI-DSS compliant handling',
      retention_policy: 'Minimal retention',
      audit_trail: 'Full audit available',
      recommendations: ['Implement PAN masking']
    }
  };

  test('POST /api/reports should accept valid report', async () => {
    const response = await request(app)
      .post('/api/reports')
      .send(validReport)
      .expect(201);
    
    expect(response.body).toHaveProperty('success', true);
    expect(response.body).toHaveProperty('report_id');
  });

  test('POST /api/reports should reject invalid report', async () => {
    const invalidReport = { ...validReport };
    delete invalidReport.metadata;
    
    await request(app)
      .post('/api/reports')
      .send(invalidReport)
      .expect(400);
  });

  test('GET /api/reports should return reports list', async () => {
    const response = await request(app)
      .get('/api/reports')
      .expect(200);
    
    expect(response.body).toHaveProperty('reports');
    expect(response.body).toHaveProperty('pagination');
  });
});

describe('Dashboard API', () => {
  test('GET /api/dashboard/stats should return statistics', async () => {
    const response = await request(app)
      .get('/api/dashboard/stats')
      .expect(200);
    
    expect(response.body).toHaveProperty('overview');
    expect(response.body.overview).toHaveProperty('total_reports');
  });
});

// Cleanup after tests
afterAll(async () => {
  const db = getDatabase();
  if (db) {
    await db.destroy();
  }
});