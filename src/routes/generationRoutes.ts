import { Router } from 'express';
import {generateAiPrediction, generateWeightedNumbers} from '../controllers/generationController';

const router = Router();

router.post('/weighted', generateWeightedNumbers);

router.post('/ai', generateAiPrediction);

export default router;

