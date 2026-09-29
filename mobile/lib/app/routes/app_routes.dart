abstract class AppRoutes {
  AppRoutes._();

  static const splash = '/splash';
  static const login = '/auth/login';
  static const register = '/auth/register';
  static const workspaces = '/workspaces';
  static const workspaceHome = '/workspaces/:id';
  static const addServer = '/workspaces/:id/servers/add';
  static const serverDetail = '/workspaces/:id/servers/:serverId';
  static const services = '/workspaces/:id/servers/:serverId/services';
  static const logs = '/workspaces/:id/servers/:serverId/services/:serviceName/logs';
  static const docker = '/workspaces/:id/servers/:serverId/docker';
  static const containerDetail = '/workspaces/:id/servers/:serverId/docker/containers/:containerId';
  static const deployments = '/workspaces/:id/servers/:serverId/deployments';
  static const backups = '/workspaces/:id/servers/:serverId/backups';
  static const alerts = '/workspaces/:id/alerts';
  static const notifications = '/workspaces/:id/notifications';
  static const auditLogs = '/workspaces/:id/audit-logs';
  static const serverTerminal = '/workspaces/:id/servers/:serverId/terminal';
}


