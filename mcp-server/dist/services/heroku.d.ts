export declare class HerokuService {
    private herokuToken;
    constructor();
    listApps(showAll?: boolean): Promise<any>;
    getAppInfo(appName: string): Promise<any>;
    deployApp(appName: string, environment: string): Promise<any>;
    scaleApp(appName: string, dynoType: string, quantity: number, size?: string): Promise<any>;
    queryDatabase(appName: string, query: string): Promise<any>;
    getAppsResource(): Promise<any>;
    getPipelineResource(): Promise<any>;
}
//# sourceMappingURL=heroku.d.ts.map