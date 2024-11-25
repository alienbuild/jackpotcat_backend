import { Request, Response } from 'express';
import prisma from '../services/prisma';

export const getSavedNumbers = async (req: Request, res: Response) => {
    try {

        const userId = req.userId;

        const savedNumbers = await prisma.savedNumbers.findFirst({
            where: { userId: userId },
        });

        if (!savedNumbers) {
            throw new Error('No saved data')
        }

        res.status(200).json(savedNumbers);

    } catch (error) {
        res.status(400).json({ error: 'Failed to retrieve saved numbers' });
    }
};
