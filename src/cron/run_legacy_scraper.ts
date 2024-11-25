import { PythonShell } from 'python-shell';
import fs from 'fs/promises';
import path from 'path';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const SCRIPT_PATH = path.resolve(__dirname, './legacy_scraper.py');
const OUTPUT_FILE = path.resolve(__dirname, './lottery_results.json');
console.log('Looking for:', OUTPUT_FILE);

export const runScraper = async (): Promise<void> => {
    try {
        console.log('Running scraper...');
        await PythonShell.run(SCRIPT_PATH, {});

        console.log('Scraper executed successfully.');

        // Read the JSON file
        console.log('Reading results...');
        const data = await fs.readFile(OUTPUT_FILE, 'utf-8');
        const results = JSON.parse(data);

        // Save the results into the database
        console.log('Saving results to the database...');
        for (const result of results) {
            const existingResult = await prisma.lotteryResult.findUnique({
                where: { drawDate: new Date(result.draw_date) },
            });

            if (!existingResult) {
                // Create the LotteryResult entry
                const lotteryResult = await prisma.lotteryResult.create({
                    data: {
                        drawDate: new Date(result.draw_date),
                        jackpot: Number(result.jackpot),
                    },
                });

                // Create LotteryNumber entries
                await prisma.lotteryNumber.createMany({
                    data: [
                        ...result.numbers.map((number: number) => ({
                            number,
                            isBonus: false,
                            resultId: lotteryResult.id,
                        })),
                        {
                            number: result.bonus_ball,
                            isBonus: true,
                            resultId: lotteryResult.id,
                        },
                    ],
                });

                console.log(`Saved result for draw date: ${result.draw_date}`);
            } else {
                console.log(`Result for draw date ${result.draw_date} already exists.`);
            }
        }

        console.log('All results saved successfully.');
    } catch (err) {
        console.error('Error during scraper execution:', err);
        throw err;
    } finally {
        await prisma.$disconnect();
    }
};

// Run the scraper
(async () => {
    try {
        await runScraper();
    } catch (err) {
        console.error('Error:', err);
    }
})();
