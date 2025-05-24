import * as yaml from 'js-yaml';
import * as fs from 'fs';
import { join } from 'path';

export default () => {
  const YAML_CONFIG_FILENAME = join(__dirname, '../../application.yaml');
  const fileContents = fs.readFileSync(YAML_CONFIG_FILENAME, 'utf8');
  return yaml.load(fileContents) as Record<string, any>;
};
