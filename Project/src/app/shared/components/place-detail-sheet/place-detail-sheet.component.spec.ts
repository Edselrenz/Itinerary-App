import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PlaceDetailSheetComponent } from './place-detail-sheet.component';
import { PlaceService } from '../../../core/services/place.service';
import { Place } from '../../../core/models/place.models';

describe('PlaceDetailSheetComponent', () => {
  let component: PlaceDetailSheetComponent;
  let fixture: ComponentFixture<PlaceDetailSheetComponent>;

  const mockPlace: Place = {
    id: 'test-sheet-place-1',
    name: 'Minalungao National Park',
    category: 'nature_park',
    latitude: 15.2981,
    longitude: 121.1223,
    municipality_name: 'General Tinio',
    address_text: 'General Tinio, Nueva Ecija',
    description: 'Scenic limestone gorge and river.',
    editorial_summary: 'Spectacular natural river park in Nueva Ecija.',
    rating: 4.6,
    user_rating_count: 1250,
    opening_hours: '08:00 AM - 05:00 PM',
    regular_opening_hours: {
      open_now: true,
      weekday_descriptions: ['Monday: 8:00 AM – 5:00 PM', 'Tuesday: 8:00 AM – 5:00 PM'],
    },
    estimated_cost_min: 100,
    estimated_cost_max: 300,
    cost_currency: 'PHP',
    source_name: 'Google Places',
    source_record_id: 'gp-123',
    imported_at: '2026-11-06T00:00:00Z',
    is_featured: true,
    tags: ['nature', 'river'],
    directions_url: 'https://maps.google.com/test',
    photos: [
      { name: 'places/gp-123/photos/photo1', width_px: 800, height_px: 600 },
      { name: 'places/gp-123/photos/photo2', width_px: 800, height_px: 600 },
    ],
    reviews: [
      {
        author_name: 'Maria Santos',
        rating: 5,
        text: 'Breathtaking limestone formations!',
        relative_publish_time_description: '2 weeks ago',
      },
    ],
  };

  const mockPlaceService = {
    formatCategoryName: vi.fn().mockReturnValue('Nature & Parks'),
    getPlaceImage: vi.fn().mockReturnValue('assets/images/minalungao.png'),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PlaceDetailSheetComponent],
      providers: [
        { provide: PlaceService, useValue: mockPlaceService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PlaceDetailSheetComponent);
    component = fixture.componentInstance;
    component.place = mockPlace;
    fixture.detectChanges();
  });

  it('should create the place detail sheet component', () => {
    expect(component).toBeTruthy();
  });

  it('should format cost accurately for various pricing tiers', () => {
    expect(component.formatCost(mockPlace)).toBe('₱100 - ₱300');

    const freePlace = { ...mockPlace, estimated_cost_min: 0, estimated_cost_max: 0 };
    expect(component.formatCost(freePlace)).toBe('Free Admission (₱0)');

    const unpricedPlace = { ...mockPlace, estimated_cost_min: null, estimated_cost_max: null };
    expect(component.formatCost(unpricedPlace)).toBe('Admission: Check on arrival');
  });

  it('should toggle weekly opening hours accordion', () => {
    expect(component.isHoursExpanded).toBe(false);
    component.toggleHours();
    expect(component.isHoursExpanded).toBe(true);
    component.toggleHours();
    expect(component.isHoursExpanded).toBe(false);
  });

  it('should report open now status from regular opening hours', () => {
    expect(component.isOpenNow).toBe(true);
    expect(component.weekdayDescriptions.length).toBe(2);
  });

  it('should switch active photo index and generate proxy photo URLs', () => {
    expect(component.activePhotoIndex).toBe(0);
    component.setActivePhoto(1);
    expect(component.activePhotoIndex).toBe(1);

    const heroUrl = component.getHeroPhotoUrl();
    expect(heroUrl).toContain('/places/photos/places%2Fgp-123%2Fphotos%2Fphoto2');
  });

  it('should emit action events when buttons are triggered', () => {
    let closed = false;
    component.closeSheet.subscribe(() => (closed = true));
    component.onClose();
    expect(closed).toBe(true);

    let startedPlace: any = null;
    component.startTripHere.subscribe((p) => (startedPlace = p));
    component.onStartTripHere();
    expect(startedPlace?.id).toBe('test-sheet-place-1');

    let customPlace: any = null;
    component.addToCustomTrip.subscribe((p) => (customPlace = p));
    component.onAddToCustomTrip();
    expect(customPlace?.id).toBe('test-sheet-place-1');

    let dayPlace: any = null;
    component.addToDay.subscribe((p) => (dayPlace = p));
    component.onAddToDay();
    expect(dayPlace?.id).toBe('test-sheet-place-1');
  });

  it('should render traveler notes and commute guide when provided', () => {
    fixture.componentRef.setInput('stopNotes', 'Bring extra water and sturdy walking shoes.');
    fixture.componentRef.setInput('commuteInfo', {
      transitMode: 'UV Express',
      departureHub: 'Cabanatuan Terminal',
      dropOffPoint: 'Minalungao Junction',
      estimatedTravelTime: '1 hr 15 mins',
      estimatedFare: '₱120',
      travelReminder: 'Tricycles are available at the junction.',
    });
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.sheet-notes-box')?.textContent).toContain('Bring extra water');
    expect(compiled.querySelector('.sheet-commute-box')?.textContent).toContain('How to get there?');
    expect(compiled.querySelector('.sheet-commute-box')?.textContent).toContain('Minalungao Junction');
  });

  it('renders accessible close button with aria-label (WCAG 2.2)', () => {
    const closeBtn = fixture.nativeElement.querySelector('.sheet-close-btn');
    expect(closeBtn).toBeTruthy();
    expect(closeBtn.getAttribute('aria-label')).toBe('Close details');
  });

  it('allows toggling favorite state for the place', () => {
    const favBtn = fixture.nativeElement.querySelector('.sheet-fav-btn');
    expect(favBtn).toBeTruthy();
    const initialFav = component.isFavorite;
    component.toggleFavorite();
    expect(component.isFavorite).toBe(!initialFav);
  });
});
