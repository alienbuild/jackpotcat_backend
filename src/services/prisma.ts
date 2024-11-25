import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export const connectToDatabase = async (): Promise<void> => {
    try {
        console.log('Attempting to connect to the database...');
        await prisma.$connect();
        console.log('Successfully connected to the database.');
    } catch (error) {
        console.error('Failed to connect to the database:', error);
        process.exit(1);
    }
};

// Optional: Cleanup on process exit
process.on('SIGINT', async () => {
    await prisma.$disconnect();
    console.log('Disconnected from the database.');
    process.exit(0);
});

export default prisma;
