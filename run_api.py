#!/usr/bin/env python3
"""Start Empirica Outreach API server"""

import sys
sys.path.insert(0, '.')
sys.path.insert(0, '../empirica')

from empirica_outreach.api import create_app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Empirica Outreach API")
    print("   Dashboard: http://localhost:8001/api/v1/outreach/")
    print("   Health: http://localhost:8001/health")
    print("")
    app.run(host="0.0.0.0", port=8001, debug=True)
