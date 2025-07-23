export declare class AIService {
    private baseUrl;
    constructor();
    performInference(appName: string, model: string, inputData: any): Promise<any>;
    batchInference(appName: string, requests: any[]): Promise<any>;
    getModelsResource(): Promise<any>;
    listAvailableModels(): Promise<any>;
    getInferenceHistory(appName: string, inferenceType: string): Promise<any>;
}
//# sourceMappingURL=ai.d.ts.map