# V2 TODO - Mediflux MVP

## High Priority (Pre-Demo)

### Document Analyzer Improvements
- [ ] **OCR Table Extraction Enhancement**: Current system extracts 0 categories instead of expected 11-12 from healthcare documents
  - Consider alternative OCR libraries (EasyOCR, PaddleOCR) as fallback
  - Implement table-specific preprocessing (morphological operations, line detection)
  - Add manual fallback patterns for critical medical codes

- [ ] **Error Handling & Fallbacks**: Implement graceful degradation when OCR fails
  - Mock data responses for demo purposes
  - Better error messages for users
  - Fallback to manual input interface

### Core Functionality
- [ ] **Complete Pattern Matching**: Finish syntax fixes in coverage table extraction logic
- [ ] **Test Coverage**: Add comprehensive tests for document analysis pipeline
- [ ] **Frontend Integration**: Connect React frontend to FastAPI backend endpoints

## Medium Priority (Post-Demo)

### Data Integration
- [ ] **BDPM API Alternative**: Implement self-hosted BDPM GraphQL service or fallback data source
  - Current endpoint returns 503 Service Unavailable
  - Consider downloading BDPM database directly and serving locally

### Performance & Reliability
- [ ] **Memory Optimization**: Implement efficient session management and data compression
- [ ] **Caching Layer**: Add Redis/SQLite caching for frequently accessed data
- [ ] **Rate Limiting**: Implement API rate limiting for external service calls

### User Experience
- [ ] **Progressive Upload**: Support drag-and-drop with progress indicators
- [ ] **Real-time Feedback**: WebSocket integration for live OCR processing updates
- [ ] **Mobile Responsiveness**: Optimize for mobile document capture

## Low Priority (Future Enhancements)

### Advanced Features
- [ ] **Multi-document Analysis**: Support batch processing of healthcare documents
- [ ] **Document Validation**: Cross-reference extracted data with known databases
- [ ] **Smart Suggestions**: AI-powered recommendations based on extracted coverage data

### Infrastructure
- [ ] **Monitoring & Analytics**: Implement logging, metrics, and error tracking
- [ ] **Security Hardening**: Add authentication, input validation, and data encryption
- [ ] **Scalability**: Prepare for horizontal scaling and load balancing

### Integrations
- [ ] **Calendar Integration**: Connect with healthcare provider booking systems
- [ ] **Payment Processing**: Integrate with reimbursement simulation tools
- [ ] **Regional Data**: Add more comprehensive geographic healthcare data

## Technical Debt
- [ ] **Code Cleanup**: Remove duplicate OCR scoring functions in handler.py
- [ ] **Type Safety**: Add comprehensive type hints throughout codebase
- [ ] **Documentation**: Add docstrings and API documentation
- [ ] **Testing**: Increase test coverage to >80%

## Known Issues to Address
- BDPM GraphQL API returning 503 errors (external dependency)
- OCR preprocessing may be too aggressive for some document types
- Pattern matching needs completion for original format documents
- Frontend-backend integration not yet implemented

## Demo Preparation
- [ ] **Sample Data**: Prepare mock responses for reliable demo experience
- [ ] **Presentation Flow**: Document key user journeys for demo
- [ ] **Backup Plans**: Prepare fallback scenarios if OCR fails during demo
