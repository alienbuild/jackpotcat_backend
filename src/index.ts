import express from 'express';
import bodyParser from 'body-parser';
import testRoutes from "./routes/testRoutes";
import generationRoutes from "./routes/generationRoutes";
import userRoutes from "./routes/userRoutes";

// Queue CRON
import './cron/scheduler';

// Connect to Prisma
import {connectToDatabase} from "./services/prisma";
import {verifyToken} from "./utils";

// Initialize Express App
const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(express.json());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Routes that do not require authentication
app.use('/api', testRoutes);

// Routes that require authentication
app.use('/api/generate', verifyToken, generationRoutes);
app.use('/api/user', verifyToken, userRoutes);

// Start the server and connect to the database
const startServer = async () => {
    try {
        await connectToDatabase();
        app.listen(PORT, () => {
            console.log(`Server running on port ${PORT}`);
        });
    } catch (error) {
        console.error('Error starting the server:', error);
        process.exit(1);
    }
};

(async () => {
    await startServer();
})();
