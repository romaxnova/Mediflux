# V2 Known Issues

## BDPM API Connectivity
- **Issue**: BDPM GraphQL API endpoint returning 503 Service Unavailable
- **Endpoint**: `https://api-bdpm-graphql.axel-op.fr/graphql`
- **Status**: External service issue, not V2 code problem
- **Impact**: Medication search functionality temporarily unavailable
- **Solution**: Consider self-hosting BDPM GraphQL service or implement fallback data source
- **Priority**: Medium (external dependency)

## Odissé API Data Mismatch - RESOLVED ✅ 
- **Issue**: Expected datasets (professional densities, appointment delays) don't exist in real Odissé API
- **Resolution**: Replaced with better data sources from data.gouv.fr "Offres de Soin" section
- **New Sources**: DREES Datasets, ScanSanté (ATIH), IQSS Quality Indicators
- **Status**: RESOLVED - Better maintained, open-access replacements identified
- **Impact**: V2 Prompt 3 scope updated with superior data sources
- **Priority**: ✅ COMPLETED

## SAE Hospital Data Integration - COMPLETED ✅
- **Achievement**: Successfully integrated 2023 hospital statistics
- **Data Processed**: 3975 hospitals, 1528 MCO activities, 620 emergency services, 101 regional metrics
- **Features**: Hospital capacity analysis, occupancy rates, availability scoring, regional density metrics
- **Use Cases**: Route users to less congested hospitals, identify high-availability facilities
- **Status**: FUNCTIONAL - Hospital recommendation system operational
- **Priority**: ✅ COMPLETED

## OpenMedic Data Access - RESOLVED ✅
- **Issue**: data.gouv.fr resource URLs redirect to ameli.fr forms requiring session handling
- **Solution**: Found direct download URL with token: `https://open-data-assurance-maladie.ameli.fr/medicaments/download_file.php?token=f11a2e714ddad5f93eea56de8410c181&file=Open_MEDIC_Base_Complete/OPEN_MEDIC_2024.zip`
- **Additional fix**: French decimal format (comma separators) needed parsing
- **Status**: WORKING - 2024 dataset downloaded (478MB CSV, 1.9M records)
- **Impact**: V2 Prompt 3 OpenMedic integration functional
- **Priority**: ✅ COMPLETED

## Notes
- All V2 modules are functional and properly integrated
- BDPM issue affects both V1 and V2 implementations equally
- Consider implementing mock responses for development testing
- SOS Médecins utility unclear - need to evaluate for MVP relevance
