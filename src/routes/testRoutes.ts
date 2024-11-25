import { Router } from 'express';
import { testRoute } from '../controllers/testController';

const router = Router();

router.get('/test', testRoute);

export default router;
