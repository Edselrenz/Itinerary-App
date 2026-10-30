import { Component, EnvironmentInjector, inject } from '@angular/core';
import {
  IonIcon,
  IonTabBar,
  IonTabButton,
  IonTabs,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
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
  imports: [IonTabs, IonTabBar, IonTabButton, IonIcon],
})
export class TabsPage {
  public environmentInjector = inject(EnvironmentInjector);

  constructor() {
    addIcons({
      home,
      locationSharp,
      timeOutline,
      personCircleOutline,
    });
  }
}
