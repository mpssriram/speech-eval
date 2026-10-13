import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import {parse} from 'yaml';
import {flaggedPhraseTests} from './flaggedPhrases.js';
const config=parse(fs.readFileSync('../configs/detector.yaml','utf8'));
flaggedPhraseTests(test,expect,'/results/0aae3748f747b13e89697e17','live',config);
