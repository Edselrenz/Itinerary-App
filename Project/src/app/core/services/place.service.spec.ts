import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { PlaceService } from './place.service';
import { environment } from '../../../environments/environment';
import {
  Municipality,
  PaginatedPlaces,
  Place,
} from '../models/place.models';

describe('PlaceService', () => {
  let service: PlaceService;
  let httpMock: HttpTestingController;

  const mockPlace: Place = {
    id: 'test-uuid-1',
    name: 'Minalungao National Park',
    category: 'nature_park',
    latitude: 15.2981,
    longitude: 121.1223,
    municipality_id: 'mun-uuid-1',
    municipality_name: 'General Tinio',
    address_text: 'Brgy. Pias, General Tinio, Nueva Ecija',
    description: 'Protected limestone canyon along Peñaranda River.',
    cost_currency: 'PHP',
    source_name: 'CuratedNuevaEcijaMVP',
    source_record_id: 'curated/minalungao',
    imported_at: '2026-10-30T10:00:00Z',
    is_featured: true,
    tags: ['nature_park', 'Family-Friendly'],
    directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223',
  };

  const mockPaginated: PaginatedPlaces = {
    total: 1,
    limit: 20,
    offset: 0,
    items: [mockPlace],
  };

  const mockMunicipalities: Municipality[] = [
    {
      id: 'mun-uuid-1',
      name: 'General Tinio',
      slug: 'general-tinio',
      is_city: false,
      center_lat: 15.349,
      center_lng: 121.049,
    },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        PlaceService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(PlaceService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('searchPlaces', () => {
    it('should query places with query parameters', () => {
      service
        .searchPlaces({
          q: 'Minalungao',
          categories: ['nature_park', 'resort_swimming'],
          featured: true,
          limit: 10,
          offset: 0,
        })
        .subscribe((res) => {
          expect(res.total).toBe(1);
          expect(res.items.length).toBe(1);
          expect(res.items[0].name).toBe('Minalungao National Park');
        });

      const req = httpMock.expectOne((r) =>
        r.url === `${environment.apiBaseUrl}/places` &&
        r.params.get('q') === 'Minalungao' &&
        r.params.get('categories') === 'nature_park,resort_swimming' &&
        r.params.get('featured') === 'true' &&
        r.params.get('limit') === '10' &&
        r.params.get('offset') === '0'
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockPaginated);
    });

    it('should query places without parameters', () => {
      service.searchPlaces().subscribe((res) => {
        expect(res.items.length).toBe(1);
      });

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/places`);
      expect(req.request.method).toBe('GET');
      req.flush(mockPaginated);
    });
  });

  describe('getFeaturedPlaces', () => {
    it('should request places with featured=true and map to items array', () => {
      service.getFeaturedPlaces(5).subscribe((items) => {
        expect(items.length).toBe(1);
        expect(items[0].name).toBe('Minalungao National Park');
      });

      const req = httpMock.expectOne(
        (r) =>
          r.url === `${environment.apiBaseUrl}/places` &&
          r.params.get('featured') === 'true' &&
          r.params.get('limit') === '5'
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockPaginated);
    });
  });

  describe('getPlaceById', () => {
    it('should fetch place by id', () => {
      service.getPlaceById('test-uuid-1').subscribe((place) => {
        expect(place.id).toBe('test-uuid-1');
        expect(place.name).toBe('Minalungao National Park');
      });

      const req = httpMock.expectOne(
        `${environment.apiBaseUrl}/places/test-uuid-1`
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockPlace);
    });
  });

  describe('getMunicipalities', () => {
    it('should fetch municipalities list with query filter', () => {
      service.getMunicipalities('Tinio').subscribe((list) => {
        expect(list.length).toBe(1);
        expect(list[0].name).toBe('General Tinio');
      });

      const req = httpMock.expectOne(
        (r) =>
          r.url === `${environment.apiBaseUrl}/municipalities` &&
          r.params.get('q') === 'Tinio'
      );
      expect(req.request.method).toBe('GET');
      req.flush(mockMunicipalities);
    });
  });

  describe('getPlaceImage', () => {
    it('should return remote image when present', () => {
      const img = service.getPlaceImage('Custom Place', 'https://example.com/custom.jpg');
      expect(img).toBe('https://example.com/custom.jpg');
    });

    it('should match curated high-resolution photography for recognized names', () => {
      expect(service.getPlaceImage('Minalungao National Park')).toBe(
        'assets/images/minalungao.png'
      );
      expect(service.getPlaceImage('Tagpuan sa Lumang Gapan')).toBe(
        'assets/images/tagpuan_gapan.png'
      );
      expect(service.getPlaceImage('Pantabangan Lake Viewpoint')).toBe(
        'assets/images/pantabangan_lake.png'
      );
    });

    it('should fallback to default asset for unrecognized places without remote image', () => {
      const fallback = service.getPlaceImage('Unknown Barangay Spot');
      expect(fallback).toBe('assets/images/minalungao.png');
    });
  });

  describe('formatCategoryName', () => {
    it('should format canonical category keys into friendly titles', () => {
      expect(service.formatCategoryName('nature_park')).toBe('Nature & Adventure');
      expect(service.formatCategoryName('cafe')).toBe('Cafe & Dining');
      expect(service.formatCategoryName('church_religious')).toBe('Heritage & Faith');
    });

    it('should replace underscores for unknown category keys', () => {
      expect(service.formatCategoryName('custom_unmapped_category')).toBe(
        'custom unmapped category'
      );
    });
  });
});

