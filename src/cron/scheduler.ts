import cron from 'node-cron';
import { exec } from 'child_process';
import path from 'path';

const SCRIPT_PATH = path.resolve(__dirname, './run_latest_scraper.ts');

export const runScraper = () => {
    console.log(`Running scraper at ${new Date().toISOString()}`);
    exec(`yarn ts-node ${SCRIPT_PATH}`, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error running scraper: ${error.message}`);
            return;
        }
        if (stderr) {
            console.error(`Scraper stderr: ${stderr}`);
        }
        console.log(`Scraper stdout: ${stdout}`);
    });
};

// Schedule to run the scraper at 8:15 PM GMT on Wednesdays and Saturdays
cron.schedule('15 20 * * 3,6', () => {
    console.log('Scheduled scraper job triggered...');
    runScraper();
});

console.log('Scheduler is running...');
