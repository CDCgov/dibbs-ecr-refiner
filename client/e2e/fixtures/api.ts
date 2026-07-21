import { APIRequestContext, expect } from '@playwright/test';

interface Configuration {
  id: string;
  name: string;
}

interface CodedConcept {
  code: string;
  display: string;
}

interface Condition {
  id: string;
  display_name: string;
  rsg_codes: CodedConcept[];
}

interface CustomCode {
  code: string;
  system_id: string;
  display: string;
}

interface System {
  id: string;
  key: string;
  display_name: string;
  oid: string;
}

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

  async uploadCustomCodeCsv(configId: string, codes: CustomCode[]) {
    const payload = [];
    for (const c of codes) {
      payload.push({ ...c });
    }
    const uploadCsvReq = await this.request.post(
      `/api/v1/configurations/${configId}/custom-codes/confirm`,
      {
        data: {
          custom_codes: payload,
        },
      }
    );

    expect(uploadCsvReq.ok()).toBeTruthy();
    const json = await uploadCsvReq.json();
    expect(json).toEqual(
      expect.objectContaining({
        errors: null,
      })
    );
  }

  async getSystems(): Promise<System[]> {
    const systemsReq = await this.request.get(`/api/v1/code-systems/`);
    expect(systemsReq.ok()).toBeTruthy();
    const json = await systemsReq.json();
    return json as System[];
  }

  async updateConfigurationStatus(
    configId: string,
    status: 'active' | 'inactive'
  ): Promise<void> {
    const urlStatus = status === 'active' ? 'activate' : 'deactivate';
    const statusUpdateReq = await this.request.patch(
      `/api/v1/configurations/${configId}/${urlStatus}`
    );
    expect(statusUpdateReq.ok()).toBeTruthy();
    const json = await statusUpdateReq.json();
    expect(json).toEqual(
      expect.objectContaining({
        status: status,
      })
    );
  }
}
