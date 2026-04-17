import { Routes } from '@angular/router';
import { TabsPage } from './tabs.page';

export const routes: Routes = [
  {
    path: 'tabs',
    component: TabsPage,
    children: [
      {
        path: 'home',
        loadComponent: () =>
          import('../home/home.page').then((m) => m.HomePage),
      },
      {
        path: 'try-on',
        loadComponent: () =>
          import('../try-on/try-on.page').then((m) => m.TryOnPage),
      },
      {
        path: 'gallery',
        loadComponent: () =>
          import('../gallery/gallery.page').then((m) => m.GalleryPage),
      },
      {
        path: 'result',
        loadComponent: () =>
          import('../result/result.page').then((m) => m.ResultPage),
      },
      {
        path: '',
        redirectTo: '/tabs/home',
        pathMatch: 'full',
      },
    ],
  },
  {
    path: '',
    redirectTo: '/tabs/home',
    pathMatch: 'full',
  },
];
