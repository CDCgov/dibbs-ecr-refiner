import { APIRequestContext, expect } from '@playwright/test';

type Configuration = {
  id: string;
  name: string;
};

type Condition = {
  id: string;
  display_name: string;
};

export class Api {
  constructor(private request: APIRequestContext) {}

  async getCondition(conditionName: string): Promise<Condition> {
    const conditionsReq = await this.request.get('/api/v1/conditions/');
    expect(conditionsReq.ok()).toBeTruthy();

    const json = await conditionsReq.json();
    expect(json).toContainEqual(
      expect.objectContaining({
        display_name: conditionName,
      })
    );

    const condition = (json as [Condition]).find(
      (c) => c.display_name === conditionName
    );
    expect(condition).toBeTruthy();
    if (!condition) {
      throw new Error(`Condition ${conditionName} could not be found.`);
    }
    return condition;
  }

  async createConfiguration(conditionName: string): Promise<Configuration> {
    const condition = await this.getCondition(conditionName);

    const configReq = await this.request.post('/api/v1/configurations/', {
      data: {
        condition_id: condition.id,
      },
    });
    expect(configReq.ok()).toBeTruthy();

    const json = await configReq.json();
    expect(json).toEqual(
      expect.objectContaining({
        name: conditionName,
      })
    );

    if (!json) {
      throw new Error(
        `Configuration for condition ${conditionName} could not be created.`
      );
    }

    return json as Configuration;
  }
}
