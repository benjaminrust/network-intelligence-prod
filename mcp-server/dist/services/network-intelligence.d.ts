export declare class NetworkIntelligenceService {
    private baseUrl;
    constructor();
    analyzeTraffic(appName: string, trafficData: any): Promise<any>;
    getNetworkStatus(appName: string): Promise<any>;
    getSecurityAlerts(appName: string): Promise<any>;
    getThreatIntelligence(appName: string): Promise<any>;
    getAnalytics(appName: string, metricName?: string): Promise<any>;
}
//# sourceMappingURL=network-intelligence.d.ts.map