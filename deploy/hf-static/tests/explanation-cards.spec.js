import {test,expect} from '@playwright/test';
import {explanationCardTests} from '../../../web/tests/explanationCards.js';
explanationCardTests(test,expect,'static');
