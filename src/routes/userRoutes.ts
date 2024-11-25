import { Router } from 'express';
import { getSavedNumbers } from '../controllers/userController';

const router = Router();

router.get('/getSavedNumbers', getSavedNumbers);

export default router;
