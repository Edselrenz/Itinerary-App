import { Component } from '@angular/core';
import {
  IonContent,
  IonHeader,
  IonIcon,
  IonTitle,
  IonToolbar,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import { mapOutline } from 'ionicons/icons';

@Component({
  selector: 'app-map',
  templateUrl: './map.page.html',
  styleUrls: ['./map.page.scss'],
  standalone: true,
  imports: [IonHeader, IonToolbar, IonTitle, IonContent, IonIcon],
})
export class MapPage {
  constructor() {
    addIcons({ mapOutline });
  }
}
