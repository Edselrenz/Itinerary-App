import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { OsmOverpassService, OverpassResponse } from './osm-overpass.service';

describe('OsmOverpassService', () => {
  let service: OsmOverpassService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        OsmOverpassService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(OsmOverpassService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should correctly map OSM tags to canonical categories', () => {
    expect(service.mapOsmTagsToCategory({ amenity: 'cafe' })).toBe('cafe');
    expect(service.mapOsmTagsToCategory({ amenity: 'restaurant' })).toBe('restaurant');
    expect(service.mapOsmTagsToCategory({ tourism: 'hotel' })).toBe('hotel_accommodation');
    expect(service.mapOsmTagsToCategory({ tourism: 'attraction' })).toBe('tourist_attraction');
    expect(service.mapOsmTagsToCategory({ tourism: 'museum' })).toBe('museum_cultural');
    expect(service.mapOsmTagsToCategory({ amenity: 'place_of_worship' })).toBe('church_religious');
    expect(service.mapOsmTagsToCategory({ leisure: 'park' })).toBe('nature_park');
    expect(service.mapOsmTagsToCategory({ leisure: 'water_park' })).toBe('resort_swimming');
    expect(service.mapOsmTagsToCategory({ amenity: 'hospital' })).toBe('hospital_clinic');
    expect(service.mapOsmTagsToCategory({ amenity: 'pharmacy' })).toBe('pharmacy');
    expect(service.mapOsmTagsToCategory({ amenity: 'bank' })).toBe('bank_atm');
    expect(service.mapOsmTagsToCategory({ amenity: 'fuel' })).toBe('fuel_station');
    expect(service.mapOsmTagsToCategory({ shop: 'supermarket' })).toBe('convenience_store');
    expect(service.mapOsmTagsToCategory({ shop: 'clothes' })).toBe('shopping_market');
  });

  it('should query Overpass API and parse response into Place objects', () => {
    const mockResponse: OverpassResponse = {
      version: 0.6,
      generator: 'Overpass API',
      elements: [
        {
          type: 'node',
          id: 123456,
          lat: 15.485,
          lon: 120.972,
          tags: {
            name: 'Artisan Cafe NE',
            amenity: 'cafe',
            'addr:city': 'Cabanatuan City',
          },
        },
        {
          type: 'way',
          id: 654321,
          center: { lat: 15.5, lon: 121.0 },
          tags: {
            name: 'Central Eco Park',
            leisure: 'park',
            'addr:city': 'Palayan City',
          },
        },
      ],
    };

    service
      .fetchLiveOsmPlaces({ minLat: 15.0, minLng: 120.0, maxLat: 16.0, maxLng: 121.5 })
      .subscribe((places) => {
        expect(places.length).toBe(2);
        expect(places[0].name).toBe('Artisan Cafe NE');
        expect(places[0].category).toBe('cafe');
        expect(places[0].latitude).toBe(15.485);
        expect(places[0].longitude).toBe(120.972);
        expect(places[0].source_name).toBe('OpenStreetMap Live');

        expect(places[1].name).toBe('Central Eco Park');
        expect(places[1].category).toBe('nature_park');
      });

    const req = httpMock.expectOne((r) => r.url.includes('overpass-api.de/api/interpreter'));
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });
});

