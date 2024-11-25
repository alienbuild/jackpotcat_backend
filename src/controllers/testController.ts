import { Request, Response } from 'express';

export const testRoute = (req: Request, res: Response) => {
    try {
        res.json({ message: 'Test route working!', timestamp: new Date().toISOString() });
    } catch (error) {
        console.error('Error in test route:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
};
