import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnChanges,
  SimpleChanges,
  ElementRef,
  HostListener,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonIcon } from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  locationSharp,
  locationOutline,
  searchOutline,
  closeCircle,
  star,
  globeOutline,
  chevronForwardOutline,
  mapOutline,
  closeOutline,
  checkmarkCircle,
} from 'ionicons/icons';

export interface DestinationSuggestion {
  label: string;
  municipality: string;
  type: 'province' | 'municipality' | 'landmark';
  placeId?: string;
  subtitle: string;
  poiCount?: number;
  district?: string;
  isCity?: boolean;
}

export const NUEVA_ECIJA_32_LGUS: Array<{
  name: string;
  district: string;
  highlights: string;
  isCity?: boolean;
  poiCount?: number;
}> = [
  { name: 'Cabanatuan City', district: 'Central', isCity: true, highlights: 'Food Trip, Cafes & WWII Heritage', poiCount: 565 },
  { name: 'Gapan City', district: 'South', isCity: true, highlights: 'Lumang Gapan Heritage Street & Local Dining', poiCount: 567 },
  { name: 'San Jose City', district: 'North', isCity: true, highlights: 'Northern Gateway, Parks & Culinary Stops', poiCount: 327 },
  { name: 'Science City of Muñoz', district: 'North-West', isCity: true, highlights: 'PhilRice, CLSU Agri-Tourism & Museums', poiCount: 206 },
  { name: 'Palayan City', district: 'Central', isCity: true, highlights: 'Provincial Capitol Hub, Nature & Resorts', poiCount: 51 },
  { name: 'Pantabangan', district: 'North-East', highlights: 'Pantabangan Lake, Dam Viewpoints & Highland Resorts', poiCount: 156 },
  { name: 'Bongabon', district: 'East', highlights: 'Farm Resorts, Rohi Cafe & Museo de Bongabon', poiCount: 93 },
  { name: 'Gabaldon', district: 'East', highlights: 'Dupinga River, Eco-Parks & Mountain Resorts', poiCount: 67 },
  { name: 'General Tinio', district: 'South-East', highlights: 'Minalungao National Park & Limestone River', poiCount: 49 },
  { name: 'Santa Rosa', district: 'Central-South', highlights: 'Family Resorts, Dining & Heritage Churches', poiCount: 299 },
  { name: 'Talavera', district: 'Central', highlights: 'Highway Dining, Farm Parks & Resorts', poiCount: 221 },
  { name: 'Laur', district: 'East', highlights: 'Scenic Mountain Views & Nature Trails', poiCount: 72 },
  { name: 'Aliaga', district: 'Central', highlights: 'Taong Putik Festival & Agriculture' },
  { name: 'Cabiao', district: 'South', highlights: 'Mt. Arayat Foothills & Nabao Lake' },
  { name: 'Carranglan', district: 'North', highlights: 'Mountain Trails, Falls & Pine Forests' },
  { name: 'Cuyapo', district: 'North-West', highlights: 'Historical Sites & Agricultural Plains' },
  { name: 'General Mamerto Natividad', district: 'Central-East', highlights: 'Nature Springs & Rural Scenery' },
  { name: 'Guimba', district: 'North-West', highlights: 'Rice Granary & Cultural Landmarks' },
  { name: 'Jaen', district: 'South', highlights: 'Churches, Local Sweets & River Views' },
  { name: 'Licab', district: 'West', highlights: 'Kariton Festival & Rural Countryside' },
  { name: 'Llanera', district: 'Central-East', highlights: 'Farmland Scenery & Agro-Tourism' },
  { name: 'Lupao', district: 'North', highlights: 'Waterfalls & Upland Farming' },
  { name: 'Nampicuan', district: 'North-West', highlights: 'Heritage Church & Peaceful Town Center' },
  { name: 'Peñaranda', district: 'South-East', highlights: 'Historic Church & Local Delicacies' },
  { name: 'Quezon', district: 'Central-West', highlights: 'Patimyas Festival & Farm Estates' },
  { name: 'Rizal', district: 'North-East', highlights: 'General Luna Shrine & Foothill Trails' },
  { name: 'San Antonio', district: 'South-West', highlights: 'Heritage Homes & Local Bakeries' },
  { name: 'San Isidro', district: 'South', highlights: 'Historic First Cry of Nueva Ecija' },
  { name: 'San Leonardo', district: 'South', highlights: 'Highway Dining & Heritage Churches' },
  { name: 'Santo Domingo', district: 'Central', highlights: 'Culinary Stops & Farm Communities' },
  { name: 'Talugtug', district: 'North', highlights: 'Rolling Hills & Upland Scenic Views' },
  { name: 'Zaragoza', district: 'South-West', highlights: 'Riverbanks & Rural Food Stops' },
];

export const NUEVA_ECIJA_TOP_LANDMARKS: Array<{
  name: string;
  municipality: string;
  subtitle: string;
  placeId?: string;
}> = [
  { name: 'Minalungao National Park', municipality: 'General Tinio', subtitle: 'Protected limestone river canyon & emerald waters' },
  { name: 'Highland Bali Villas Resort and Spa', municipality: 'Pantabangan', subtitle: 'Balinese luxury hillside resort with lake panorama' },
  { name: 'Pantabangan Dam and Lake Viewpoint', municipality: 'Pantabangan', subtitle: 'Largest earth-fill dam in Southeast Asia' },
  { name: 'Camp Pangatian War Memorial Shrine', municipality: 'Cabanatuan City', subtitle: 'Historic WWII Great Raid rescue site' },
  { name: 'PhilRice & Rice Science Museum', municipality: 'Science City of Muñoz', subtitle: 'Agricultural science & national rice research hub' },
  { name: 'Dupinga River & Eco-Park', municipality: 'Gabaldon', subtitle: 'Crystal mountain river & natural rock formations' },
  { name: 'Lumang Gapan Heritage Street', municipality: 'Gapan City', subtitle: 'Restored colonial-era brick street with night illuminations' },
  { name: 'Rohi Paperflower Cafe', municipality: 'Bongabon', subtitle: 'Boutique farm cafe amid mountain scenery' },
  { name: 'Lake Farm De La Marre', municipality: 'Pantabangan', subtitle: 'Scenic agricultural eco-farm by the lake' },
  { name: 'Tanawan Viewdeck', municipality: 'Bongabon', subtitle: 'Sweeping panoramic view of Sierra Madre mountain range' },
  { name: 'Fort Magsaysay / Col. Juan Pajota Shrine', municipality: 'Palayan City', subtitle: 'Military reservation memorial and historical landmark' },
  { name: 'Mt. 387 (Batong Amat)', municipality: 'Carranglan', subtitle: 'Famous Chocolate Hills of the North hiking trail' },
];

export function normalizeText(str: string): string {
  return (str || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

@Component({
  selector: 'app-destination-autocomplete',
  templateUrl: './destination-autocomplete.component.html',
  styleUrls: ['./destination-autocomplete.component.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule, IonIcon],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DestinationAutocompleteComponent implements OnInit, OnChanges {
  @Input() public destination: string = '';
  @Input() public placeholder: string = 'Choose a destination or landmark';
  @Input() public inputId: string = 'destination-autocomplete-input';
  @Input() public ariaLabel: string = 'Destination';

  @Output() public destinationChange = new EventEmitter<string>();
  @Output() public destinationSelected = new EventEmitter<{
    destination: string;
    placeId?: string;
    type: 'province' | 'municipality' | 'landmark';
  }>();

  public query: string = '';
  public isOpen: boolean = false;
  public showAllTownsModal: boolean = false;
  public activeDistrictTab: 'All' | 'Central' | 'North' | 'South' | 'East' = 'All';

  public filteredProvince: DestinationSuggestion[] = [];
  public filteredMunicipalities: DestinationSuggestion[] = [];
  public filteredLandmarks: DestinationSuggestion[] = [];

  public readonly allLgus = NUEVA_ECIJA_32_LGUS;
  public readonly topLandmarks = NUEVA_ECIJA_TOP_LANDMARKS;

  constructor(
    private readonly elementRef: ElementRef,
    private readonly cdr: ChangeDetectorRef
  ) {
    addIcons({
      locationSharp,
      locationOutline,
      searchOutline,
      closeCircle,
      star,
      globeOutline,
      chevronForwardOutline,
      mapOutline,
      closeOutline,
      checkmarkCircle,
    });
  }

  public ngOnInit(): void {
    this.query = this.destination || '';
    this.filterSuggestions();
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['destination']) {
      this.query = this.destination || '';
      this.cdr.markForCheck();
    }
  }

  @HostListener('document:click', ['$event'])
  public onDocumentClick(event: MouseEvent): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.isOpen = false;
      this.cdr.markForCheck();
    }
  }

  public onInputFocus(): void {
    this.isOpen = true;
    this.filterSuggestions();
    this.cdr.markForCheck();
  }

  public onInputChange(): void {
    this.isOpen = true;
    this.destinationChange.emit(this.query);
    this.filterSuggestions();
    this.cdr.markForCheck();
  }

  public clearInput(event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.query = '';
    this.destination = '';
    this.destinationChange.emit('');
    this.filterSuggestions();
    this.isOpen = true;
    this.cdr.markForCheck();
  }

  public selectSuggestion(suggestion: DestinationSuggestion): void {
    this.query = suggestion.label;
    this.destination = suggestion.municipality;
    this.isOpen = false;
    this.destinationChange.emit(suggestion.municipality);
    this.destinationSelected.emit({
      destination: suggestion.municipality,
      placeId: suggestion.placeId,
      type: suggestion.type,
    });
    this.cdr.markForCheck();
  }

  public selectTownFromModal(townName: string): void {
    this.query = townName;
    this.destination = townName;
    this.showAllTownsModal = false;
    this.isOpen = false;
    this.destinationChange.emit(townName);
    this.destinationSelected.emit({
      destination: townName,
      type: townName === 'Nueva Ecija' ? 'province' : 'municipality',
    });
    this.cdr.markForCheck();
  }

  public openAllTownsModal(event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.isOpen = false;
    this.showAllTownsModal = true;
    this.cdr.markForCheck();
  }

  public closeAllTownsModal(): void {
    this.showAllTownsModal = false;
    this.cdr.markForCheck();
  }

  public setDistrictTab(tab: 'All' | 'Central' | 'North' | 'South' | 'East'): void {
    this.activeDistrictTab = tab;
    this.cdr.markForCheck();
  }

  public getModalTowns(): Array<{ name: string; district: string; highlights: string; isCity?: boolean; poiCount?: number }> {
    if (this.activeDistrictTab === 'All') {
      return this.allLgus;
    }
    return this.allLgus.filter((lgu) => lgu.district.toLowerCase().includes(this.activeDistrictTab.toLowerCase()));
  }

  public filterSuggestions(): void {
    const q = normalizeText(this.query);

    // 1. Province Option
    if (!q || 'all of nueva ecija'.includes(q) || 'nueva ecija'.includes(q)) {
      this.filteredProvince = [
        {
          label: 'All of Nueva Ecija',
          municipality: 'Nueva Ecija',
          type: 'province',
          subtitle: 'Best multi-town provincial corridor',
          poiCount: 2673,
        },
      ];
    } else {
      this.filteredProvince = [];
    }

    // 2. Municipalities & Cities
    if (!q) {
      // Default: top hubs first
      this.filteredMunicipalities = this.allLgus.slice(0, 8).map((m) => ({
        label: m.name,
        municipality: m.name,
        type: 'municipality',
        subtitle: m.highlights,
        poiCount: m.poiCount,
        district: m.district,
        isCity: m.isCity,
      }));
    } else {
      this.filteredMunicipalities = this.allLgus
        .filter((m) => {
          const normName = normalizeText(m.name);
          const normDistrict = normalizeText(m.district);
          const normHighlights = normalizeText(m.highlights);
          return normName.includes(q) || normDistrict.includes(q) || normHighlights.includes(q);
        })
        .map((m) => ({
          label: m.name,
          municipality: m.name,
          type: 'municipality',
          subtitle: m.highlights,
          poiCount: m.poiCount,
          district: m.district,
          isCity: m.isCity,
        }));
    }

    // 3. Specific Landmarks
    if (!q) {
      this.filteredLandmarks = this.topLandmarks.slice(0, 4).map((l) => ({
        label: l.name,
        municipality: l.municipality,
        type: 'landmark',
        placeId: l.placeId,
        subtitle: `${l.municipality} • ${l.subtitle}`,
      }));
    } else {
      this.filteredLandmarks = this.topLandmarks
        .filter((l) => {
          const normName = normalizeText(l.name);
          const normMuni = normalizeText(l.municipality);
          const normSub = normalizeText(l.subtitle);
          return normName.includes(q) || normMuni.includes(q) || normSub.includes(q);
        })
        .map((l) => ({
          label: l.name,
          municipality: l.municipality,
          type: 'landmark',
          placeId: l.placeId,
          subtitle: `${l.municipality} • ${l.subtitle}`,
        }));
    }
  }
}
