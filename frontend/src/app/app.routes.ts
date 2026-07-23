import { Routes } from '@angular/router';
import { authGuard } from './core/auth.guard';
import { internalModulesGuard } from './core/module-access.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login').then((m) => m.LoginPage),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./layout/layout').then((m) => m.Layout),
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/dashboard/dashboard').then((m) => m.DashboardPage),
      },
      {
        path: 'tickets',
        loadComponent: () => import('./pages/tickets/tickets').then((m) => m.TicketsPage),
      },
      {
        path: 'tickets/nuevo',
        loadComponent: () =>
          import('./pages/ticket-create/ticket-create').then((m) => m.TicketCreatePage),
      },
      {
        path: 'tickets/:id',
        loadComponent: () =>
          import('./pages/ticket-detail/ticket-detail').then((m) => m.TicketDetailPage),
      },
      {
        path: 'inventario',
        canActivate: [internalModulesGuard],
        data: { titulo: 'Inventario' },
        loadComponent: () =>
          import('./pages/inactive-module/inactive-module').then((m) => m.InactiveModulePage),
      },
      {
        path: 'proyectos',
        canActivate: [internalModulesGuard],
        data: { titulo: 'Proyectos' },
        loadComponent: () =>
          import('./pages/inactive-module/inactive-module').then((m) => m.InactiveModulePage),
      },
      {
        path: 'conocimiento',
        canActivate: [internalModulesGuard],
        loadComponent: () =>
          import('./pages/knowledge/knowledge').then((m) => m.KnowledgePage),
      },
      {
        path: 'conocimiento/:id',
        canActivate: [internalModulesGuard],
        loadComponent: () =>
          import('./pages/knowledge-trace/knowledge-trace').then((m) => m.KnowledgeTracePage),
      },
      {
        path: 'configuracion',
        loadComponent: () =>
          import('./pages/settings/settings').then((m) => m.SettingsPage),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
