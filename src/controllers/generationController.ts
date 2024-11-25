import { Request, Response } from 'express';
import prisma from '../services/prisma';
import {PythonShell, Options} from "python-shell";

export const generateWeightedNumbers = async (req: Request, res: Response) => {
    try {

        // Fetch all lottery results from the database
        const results = await prisma.lotteryResult.findMany({
            include: {
                numbers: true,
            }
        });

        const allNumbers = results.flatMap(result => result.numbers.map(number => number.number));

        // Calculate frequency of numbers
        const frequencyMap: { [key: number]: number } = {};
        for (const num of allNumbers) {
            frequencyMap[num] = (frequencyMap[num] || 0) + 1;
        }

        // Identify hot and cold numbers
        const hotNumbers = Object.entries(frequencyMap)
            .sort(([, a], [, b]) => b - a)  // Sort by frequency (highest first)
            .map(([num, freq]) => ({
                number: parseInt(num),
                weight: freq
            }));

        const coldNumbers = Object.entries(frequencyMap)
            .sort(([, a], [, b]) => a - b)  // Sort by frequency (lowest first)
            .map(([num, freq]) => ({
                number: parseInt(num),
                weight: freq
            }));

        // Introduce randomness: select 5 hot numbers and 1 cold number
        const getRandomWeighted = (numbers: { number: number, weight: number }[], count: number) => {
            const totalWeight = numbers.reduce((sum, num) => sum + num.weight, 0);
            const selectedNumbers: number[] = [];
            const selectedSet = new Set<number>();  // To ensure uniqueness

            while (selectedNumbers.length < count) {
                const randomWeight = Math.random() * totalWeight;
                let cumulativeWeight = 0;
                for (const num of numbers) {
                    cumulativeWeight += num.weight;
                    if (cumulativeWeight >= randomWeight && !selectedSet.has(num.number)) {
                        selectedNumbers.push(num.number);
                        selectedSet.add(num.number);
                        break;
                    }
                }
            }

            return selectedNumbers;
        };

        // Select 5 hot numbers and 1 cold number
        const weightedHotNumbers = getRandomWeighted(hotNumbers.slice(0, 10), 5);  // Top 10 hot numbers
        const weightedColdNumbers = getRandomWeighted(coldNumbers.slice(0, 10), 1);  // Top 10 cold numbers

        // Combine hot and cold numbers
        let numbers = [...weightedHotNumbers, ...weightedColdNumbers];

        // Ensure that we have exactly 7 unique numbers
        while (numbers.length < 7) {
            const newNumber = Math.floor(Math.random() * 49) + 1;  // Ensure random number is between 1 and 49
            if (!numbers.includes(newNumber)) {
                numbers.push(newNumber);
            }
        }

        // If any number is greater than 49, replace it with a valid number between 1-49
        numbers = numbers.map(num => Math.min(49, Math.max(1, num)));  // Clamps each number to the range [1, 49]

        // Ensure all numbers are unique
        numbers = [...new Set(numbers)];

        // If there are still fewer than 7 unique numbers, fill in with random numbers
        while (numbers.length < 7) {
            const newRandomNumber = Math.floor(Math.random() * 49) + 1;
            numbers.push(newRandomNumber);
            numbers = [...new Set(numbers)];  // Enforce uniqueness
        }

        res.status(200).json({ prediction: numbers });
    } catch (error) {
        console.error('Error generating weighted numbers:', error);
        res.status(500).json({ error: 'Failed to generate numbers.' });
    }
};

export const generateAiPrediction = (req: Request, res: Response) => {
    const options: Options = {
        mode: 'text',
        pythonPath: 'py',  // Depending on OS and installation this may need to be 'py' or 'python3'
        scriptPath: 'src/ai',
        args: []
    };

    // Running the Python script
    PythonShell.run('predict.py', options)
        .then(results => {
            const cleanOutput = results.join('');
            const predictionLine = cleanOutput.split('\n').find(line => line.includes('Predicted Numbers'));

            if (predictionLine) {
                const prediction = predictionLine.replace('Predicted Numbers:', '').trim();
                const numbersArray = prediction
                    .replace(/\[|\]/g, '')  // Remove square brackets
                    .split(/\s+/)           // Split by any whitespace
                    .map(Number)            // Convert each item to a number
                    .filter(num => num > 0);  // Ensure only positive numbers

                res.status(200).json({ prediction: numbersArray });
            } else {
                res.status(500).json({ error: 'Failed to parse generate numbers.' });
            }
        })
        .catch(error => {
            res.status(500).json({ error: 'Failed to generate numbers.' });
        });
};