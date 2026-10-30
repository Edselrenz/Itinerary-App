import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import {
  IonButton,
  IonContent,
  IonHeader,
  IonIcon,
  IonModal,
  IonToolbar,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  arrowForward,
  calendarOutline,
  closeCircle,
  closeOutline,
  compassOutline,
  informationCircle,
  locationOutline,
  mapOutline,
  navigateOutline,
  notifications,
  openOutline,
  personCircleOutline,
  searchOutline,
  sparkles,
} from 'ionicons/icons';
import { GuestStorageService } from '../../core/services/guest-storage.service';

export interface DestinationItem {
  id: string;
  name: string;
  municipality: string;
  category: string;
  image: string;
  description: string;
  tags: string[];
  searchQuery: string;
}

@Component({
  selector: 'app-home',
  templateUrl: './home.page.html',
  styleUrls: ['./home.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    IonHeader,
    IonToolbar,
    IonContent,
    IonButton,
    IonIcon,
    IonModal,
  ],
})
export class HomePage implements OnInit {
  public isGuestMode = false;
  public searchTerm = '';
  public selectedDestination: DestinationItem | null = null;
  public isDetailModalOpen = false;

  public destinations: DestinationItem[] = [
    {
      id: 'minalungao',
      name: 'Minalungao National Park',
      municipality: 'General Tinio',
      category: 'Nature & Adventure',
      image: 'assets/images/minalungao.png',
      description: 'Towering 16-meter limestone cliffs, emerald-green Peñaranda River bamboo rafting, and subterranean caves.',
      tags: ['Balsa Rafting', 'Cliff Diving', 'Caving'],
      searchQuery: 'Minalungao National Park General Tinio Nueva Ecija',
    },
    {
      id: 'tagpuan_gapan',
      name: 'Tagpuan sa Lumang Gapan',
      municipality: 'Gapan City',
      category: 'Heritage & Culture',
      image: 'assets/images/tagpuan_gapan.png',
      description: 'The "Little Vigan" of Nueva Ecija featuring restored Spanish colonial street lamps, historic brick facades, and night food stalls.',
      tags: ['Colonial Walk', 'Night Market', 'Historic Street'],
      searchQuery: 'Tagpuan sa Lumang Gapan Gapan City Nueva Ecija',
    },
    {
      id: 'pantabangan_lake',
      name: 'Pantabangan Lake',
      municipality: 'Pantabangan',
      category: 'Scenic & Water',
      image: 'assets/images/pantabangan_lake.png',
      description: 'One of Southeast Asia\'s largest clean water reservoirs, framed by scenic Sierra Madre mountain ridges and bass fishing spots.',
      tags: ['Bass Fishing', 'Scenic View', 'Dam Site'],
      searchQuery: 'Pantabangan Lake Dam Pantabangan Nueva Ecija',
    },
    {
      id: 'george_point',
      name: 'George Point',
      municipality: 'Pantabangan',
      category: 'Viewpoint & Dining',
      image: 'assets/images/george_point.png',
      description: 'Scenic panoramic hilltop overlooking Pantabangan Lake, ideal for sunset views, relaxing lakeside dining, and coffee.',
      tags: ['Sunset View', 'Lakeside Coffee', 'Photography'],
      searchQuery: 'George Point Pantabangan Nueva Ecija',
    },
    {
      id: 'highland_bali',
      name: 'Highland Bali Villa Resort',
      municipality: 'Pantabangan',
      category: 'Resort & Staycation',
      image: 'assets/images/highland_bali.png',
      description: 'Balinese-inspired lakefront retreat with water sports, exotic villas, and breathtaking vistas across the water.',
      tags: ['Water Sports', 'Resort Villas', 'Spa'],
      searchQuery: 'Highland Bali Villa Resort Pantabangan Nueva Ecija',
    },
    {
      id: 'farm_villaronte',
      name: 'Farm Villaronte',
      municipality: 'San Jose City',
      category: 'Agri-Tourism',
      image: 'assets/images/farm_villaronte.png',
      description: 'Vibrant flower farm, organic produce picking, rustic pavilions, and family-friendly agro-tourism trails.',
      tags: ['Sunflower Fields', 'Organic Produce', 'Agri-Tour'],
      searchQuery: 'Farm Villaronte San Jose City Nueva Ecija',
    },
    {
      id: 'casa_batik',
      name: 'Casa Batik & Craft Gallery',
      municipality: 'Cabanatuan City',
      category: 'Art & Dining',
      image: 'assets/images/casa_batik.png',
      description: 'Artisan craft space celebrating Philippine textile traditions, local handcrafted coffee, and homegrown culinary heritage.',
      tags: ['Handcrafted Goods', 'Art Cafe', 'Local Heritage'],
      searchQuery: 'Casa Batik Cabanatuan City Nueva Ecija',
    },
    {
      id: 'pavillion_farm',
      name: 'Pavillion Farm',
      municipality: 'Bongabon',
      category: 'Eco-Park',
      image: 'assets/images/pavillion_farm.png',
      description: 'Sprawling eco-tourism estate in the Onion Capital with open lawns, fresh mountain breezes, and native dining.',
      tags: ['Mountain View', 'Onion Capital', 'Eco Camp'],
      searchQuery: 'Pavillion Farm Bongabon Nueva Ecija',
    },
  ];

  constructor(
    private guestStorage: GuestStorageService,
    private router: Router,
    private toastController: ToastController
  ) {
    addIcons({
      notifications,
      personCircleOutline,
      informationCircle,
      sparkles,
      mapOutline,
      arrowForward,
      searchOutline,
      closeCircle,
      closeOutline,
      locationOutline,
      calendarOutline,
      compassOutline,
      navigateOutline,
      openOutline,
    });
  }

  public ngOnInit(): void {
    this.guestStorage.isGuestMode$.subscribe((mode) => {
      this.isGuestMode = mode;
    });
  }

  public async onNotificationClick(): Promise<void> {
    const toast = await this.toastController.create({
      message: "You're all caught up! No active travel alerts in Nueva Ecija.",
      duration: 2500,
      position: 'top',
      color: 'dark',
    });
    await toast.present();
  }

  public onSeeAll(): void {
    this.router.navigate(['/tabs/map']);
  }

  public get filteredDestinations(): DestinationItem[] {
    const term = this.searchTerm.trim().toLowerCase();
    if (!term) {
      return this.destinations;
    }
    return this.destinations.filter(
      (d) =>
        d.name.toLowerCase().includes(term) ||
        d.municipality.toLowerCase().includes(term) ||
        d.category.toLowerCase().includes(term) ||
        d.tags.some((tag) => tag.toLowerCase().includes(term))
    );
  }

  public clearSearch(): void {
    this.searchTerm = '';
  }

  public openDestinationDetail(destination: DestinationItem): void {
    this.selectedDestination = destination;
    this.isDetailModalOpen = true;
  }

  public closeDestinationDetail(): void {
    this.isDetailModalOpen = false;
    this.selectedDestination = null;
  }

  public openInGoogleMaps(destination: DestinationItem): void {
    const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
      destination.searchQuery
    )}`;
    window.open(url, '_blank');
  }

  public startPlanningWithDestination(destination: DestinationItem): void {
    this.closeDestinationDetail();
    this.router.navigate(['/tabs/map'], {
      queryParams: { destination: destination.name, municipality: destination.municipality },
    });
  }
}
