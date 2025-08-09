/**
 * BDPM Client Fix for Updated Government URLs
 * 
 * The French government changed their download URLs from:
 * OLD: /telechargement.php?fichier=FILENAME.txt  
 * NEW: /download/file/FILENAME.txt
 * 
 * This is the corrected downloadFile function for src/bdpm_client.js
 */

const https = require('https');

function downloadFile(filename, {
    protocol = "https:",
    host = process.env.BDPM_URL_HOST || "base-donnees-publique.medicaments.gouv.fr",
    path = process.env.BDPM_URL_PATH || "/download/file"
} = {}) {
    return new Promise((resolve, reject) => {
        // Fixed URL structure - now uses /download/file/FILENAME.txt instead of query parameter
        const url = new URL(`${protocol}//${host}${path}/${filename}.txt`);
        const timer = `Downloaded ${filename}`;
        console.time(timer);
        const req = https.request(url, res => {
            if (res.statusCode !== 200) {
                reject(`Error downloading ${filename}: ${res.statusCode} ${res.statusMessage}`);
                res.resume();
                return;
            }
            res.setEncoding('latin1');
            let data = '';
            res.on('data', d => { data += d; });
            res.on('end', () => {
                console.timeEnd(timer);
                resolve(data);
            });
        })
        req.on('error', e => reject(e));
        req.end();
    });
}

module.exports = {
    downloadFile
}
