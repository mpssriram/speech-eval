import {test,expect} from '@playwright/test';
import {explanationCardTests} from './explanationCards.js';
explanationCardTests(test,expect,'dashboard');
