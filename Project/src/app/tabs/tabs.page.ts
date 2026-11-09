import { Component, EnvironmentInjector, inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  IonIcon,
  IonLabel,
  IonTabBar,
  IonTabButton,
  IonTabs,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  bookmarkOutline,
  home,
  locationSharp,
  personCircleOutline,
  timeOutline,
} from 'ionicons/icons';

@Component({
  selector: 'app-tabs',
  templateUrl: 'tabs.page.html',
  styleUrls: ['tabs.page.scss'],
  standalone: true,
  imports: [IonTabs, IonTabBar, IonTabButton, IonIcon, IonLabel],
})
export class TabsPage {
  public environmentInjector = inject(EnvironmentInjector);
  private router = inject(Router);

  constructor() {
    addIcons({
      home,
      locationSharp,
      bookmarkOutline,
      timeOutline,
      personCircleOutline,
    });
  }

  public onMapTabClicked(_event?: Event): void {
    // Explicitly navigate without query parameters so map tab always resets to general discovery mode
    this.router.navigate(['/tabs/map'], { queryParams: {} });
  }
}
