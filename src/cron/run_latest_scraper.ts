import { PythonShell } from 'python-shell';
import path from 'path';

const SCRIPT_PATH = path.resolve(__dirname, './latest_scraper.py');

export const runLatestScraper = async (): Promise<void> => {
    try {
        console.log('Checking for latest results...');
        await PythonShell.run(SCRIPT_PATH, {});

        console.log('Latest results scraper executed successfully.');
    } catch (err) {
        console.error('Error during latest scraper execution:', err);
    }
};

(async () => {
    try {
        await runLatestScraper();
    } catch (err) {
        console.error('Error:', err);
    }
})();
