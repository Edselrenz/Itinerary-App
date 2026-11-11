import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { ToastController } from '@ionic/angular';
import { of } from 'rxjs';

import { FavoritesPage } from './favorites.page';
import { FavoritesService } from '../../core/services/favorites.service';
import { PlaceService } from '../../core/services/place.service';
import type { Place } from '../../core/models/place.models';

describe('FavoritesPage', () => {
  let component: FavoritesPage;
  let fixture: ComponentFixture<FavoritesPage>;
  let favoritesServiceSpy: any;
  let placeServiceSpy: any;
  let routerSpy: any;
  let toastControllerSpy: any;

  const mockPlaces: Place[] = [
    {
      id: 'p-1',
      name: 'Minalungao National Park',
      municipality_name: 'General Tinio',
      category: 'Nature & Parks',
      latitude: 15.2981,
      longitude: 121.1223,
      estimated_cost_min: 100,
      estimated_cost_max: 300,
      cost_currency: 'PHP',
      source_name: 'manual',
      source_record_id: '1',
      imported_at: '2026-11-10T00:00:00Z',
      is_featured: true,
      tags: ['Nature'],
      directions_url: 'https://maps.google.com/?q=15.2981,121.1223',
    },
    {
      id: 'p-2',
      name: 'Highland Bali Villas',
      municipality_name: 'Pantabangan',
      category: 'Resorts & Stays',
      latitude: 15.821,
      longitude: 121.145,
      estimated_cost_min: 3500,
      estimated_cost_max: 6000,
      cost_currency: 'PHP',
      source_name: 'manual',
      source_record_id: '2',
      imported_at: '2026-11-10T00:00:00Z',
      is_featured: true,
      tags: ['Resort'],
      directions_url: 'https://maps.google.com/?q=15.821,121.145',
    },
  ];

  beforeEach(async () => {
    favoritesServiceSpy = {
      favorites$: of(mockPlaces),
      getFavorites: vi.fn().mockReturnValue(mockPlaces),
      removeFavorite: vi.fn(),
      isFavorite: vi.fn().mockReturnValue(true),
    };

    placeServiceSpy = {
      getPlaceImage: vi.fn().mockReturnValue('assets/images/minalungao.png'),
    };

    routerSpy = {
      navigate: vi.fn(),
    };

    toastControllerSpy = {
      create: vi.fn().mockResolvedValue({
        present: vi.fn().mockResolvedValue(undefined),
      }),
    };

    await TestBed.configureTestingModule({
      imports: [FavoritesPage],
      providers: [
        { provide: FavoritesService, useValue: favoritesServiceSpy },
        { provide: PlaceService, useValue: placeServiceSpy },
        { provide: Router, useValue: routerSpy },
        { provide: ToastController, useValue: toastControllerSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(FavoritesPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the favorites page', () => {
    expect(component).toBeTruthy();
    expect(component.allFavorites.length).toBe(2);
    expect(component.filteredFavorites.length).toBe(2);
  });

  it('should filter favorites by search query', () => {
    component.searchControl.setValue('minalungao');
    expect(component.filteredFavorites.length).toBe(1);
    expect(component.filteredFavorites[0].name).toBe('Minalungao National Park');

    component.clearSearch();
    expect(component.searchControl.value).toBe('');
    expect(component.filteredFavorites.length).toBe(2);
  });

  it('should filter favorites by category', () => {
    component.selectCategory('Resorts & Stays');
    expect(component.filteredFavorites.length).toBe(1);
    expect(component.filteredFavorites[0].name).toBe('Highland Bali Villas');

    component.selectCategory('ALL');
    expect(component.filteredFavorites.length).toBe(2);
  });

  it('should remove place from favorites and present toast', async () => {
    await component.removeFavorite(mockPlaces[0]);
    expect(favoritesServiceSpy.removeFavorite).toHaveBeenCalledWith('p-1');
    expect(toastControllerSpy.create).toHaveBeenCalled();
  });

  it('should open and close place detail sheet', () => {
    component.openPlaceDetail(mockPlaces[0]);
    expect(component.selectedPlaceForDetail).toEqual(mockPlaces[0]);

    component.closePlaceDetail();
    expect(component.selectedPlaceForDetail).toBeNull();
  });

  it('should navigate to map when goToMap is triggered', () => {
    component.goToMap();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/tabs/map']);
  });
});
