// Test script to verify the URL fix works
const https = require('https');

function testDownload(filename, path) {
    return new Promise((resolve, reject) => {
        const url = new URL(`https://base-donnees-publique.medicaments.gouv.fr${path}/${filename}.txt`);
        console.log(`Testing URL: ${url.toString()}`);
        
        const req = https.request(url, { method: 'HEAD' }, res => {
            console.log(`Status: ${res.statusCode} ${res.statusMessage}`);
            resolve(res.statusCode);
        });
        
        req.on('error', e => {
            console.error(`Error: ${e.message}`);
            reject(e);
        });
        
        req.end();
    });
}

async function runTests() {
    console.log('Testing URL fixes for BDPM API...\n');
    
    // Test old URL (should fail)
    console.log('1. Testing old URL structure:');
    try {
        await testDownload('CIS_bdpm', '/telechargement.php');
    } catch (e) {
        console.log('Failed as expected\n');
    }
    
    // Test new URL (should work)
    console.log('2. Testing new URL structure:');
    try {
        await testDownload('CIS_bdpm', '/download/file');
    } catch (e) {
        console.log('Failed unexpectedly\n');
    }
    
    console.log('\nDone!');
}

runTests();
