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
  heart,
  heartOutline,
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
      heart,
      heartOutline,
      bookmarkOutline,
      timeOutline,
      personCircleOutline,
    });
  }

  public onMapTabClicked(_event?: Event): void {
    // If traveler is currently following an active route on the map, preserve route navigation state (Finding 7)
    if (this.router.url.includes('followRoute=true') || this.router.url.includes('routeItineraryId=')) {
      return;
    }
    // Otherwise reset to general discovery mode
    this.router.navigate(['/tabs/map'], { queryParams: {} });
  }
}
