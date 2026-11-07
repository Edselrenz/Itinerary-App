import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  DestinationAutocompleteComponent,
  normalizeText,
  NUEVA_ECIJA_32_LGUS,
} from './destination-autocomplete.component';

describe('DestinationAutocompleteComponent', () => {
  let component: DestinationAutocompleteComponent;
  let fixture: ComponentFixture<DestinationAutocompleteComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DestinationAutocompleteComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(DestinationAutocompleteComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component with all 32 LGUs indexed', () => {
    expect(component).toBeTruthy();
    expect(component.allLgus.length).toBe(32);
    expect(NUEVA_ECIJA_32_LGUS.length).toBe(32);
  });

  describe('normalizeText (Unicode NFD Diacritic Stripping)', () => {
    it('should strip Spanish tildes and accents', () => {
      expect(normalizeText('Science City of Muñoz')).toBe('science city of munoz');
      expect(normalizeText('Peñaranda')).toBe('penaranda');
      expect(normalizeText('  SAN JOSE CITY  ')).toBe('san jose city');
    });

    it('should match unaccented queries against accented municipality names', () => {
      const q = normalizeText('munoz');
      const matches = component.allLgus.filter((m) =>
        normalizeText(m.name).includes(q)
      );
      expect(matches.length).toBe(1);
      expect(matches[0].name).toBe('Science City of Muñoz');
    });
  });

  describe('Dropdown Autocomplete Filtering', () => {
    it('should open dropdown on input focus and show default suggestions', () => {
      component.onInputFocus();
      expect(component.isOpen).toBe(true);
      expect(component.filteredProvince.length).toBe(1);
      expect(component.filteredProvince[0].label).toBe('All of Nueva Ecija');
      expect(component.filteredMunicipalities.length).toBeGreaterThan(0);
      expect(component.filteredLandmarks.length).toBeGreaterThan(0);
    });

    it('should filter suggestions when typing a partial municipality name', () => {
      component.query = 'panta';
      component.filterSuggestions();

      expect(component.filteredMunicipalities.some((m) => m.label === 'Pantabangan')).toBe(true);
      expect(component.filteredLandmarks.some((l) => l.label.includes('Pantabangan'))).toBe(true);
    });

    it('should find landmark Minalungao and resolve parent General Tinio', () => {
      component.query = 'minalungao';
      component.filterSuggestions();

      const landmark = component.filteredLandmarks.find((l) =>
        l.label.includes('Minalungao')
      );
      expect(landmark).toBeDefined();
      expect(landmark?.municipality).toBe('General Tinio');
      expect(landmark?.type).toBe('landmark');
    });

    it('should emit destinationChange and destinationSelected when selecting a suggestion', () => {
      vi.spyOn(component.destinationChange, 'emit');
      vi.spyOn(component.destinationSelected, 'emit');

      component.selectSuggestion({
        label: 'Cabanatuan City',
        municipality: 'Cabanatuan City',
        type: 'municipality',
        subtitle: 'Food Trip',
      });

      expect(component.query).toBe('Cabanatuan City');
      expect(component.destination).toBe('Cabanatuan City');
      expect(component.isOpen).toBe(false);
      expect(component.destinationChange.emit).toHaveBeenCalledWith('Cabanatuan City');
      expect(component.destinationSelected.emit).toHaveBeenCalledWith({
        destination: 'Cabanatuan City',
        placeId: undefined,
        type: 'municipality',
      });
    });

    it('should clear input on clearInput()', () => {
      vi.spyOn(component.destinationChange, 'emit');
      component.query = 'Pantabangan';
      component.clearInput();

      expect(component.query).toBe('');
      expect(component.destination).toBe('');
      expect(component.destinationChange.emit).toHaveBeenCalledWith('');
      expect(component.isOpen).toBe(true);
    });
  });

  describe('Regional Explorer Modal (All 32 LGUs)', () => {
    it('should open and close the modal', () => {
      component.openAllTownsModal();
      expect(component.showAllTownsModal).toBe(true);
      expect(component.isOpen).toBe(false);

      component.closeAllTownsModal();
      expect(component.showAllTownsModal).toBe(false);
    });

    it('should filter modal towns by district tabs', () => {
      component.setDistrictTab('All');
      expect(component.getModalTowns().length).toBe(32);

      component.setDistrictTab('North');
      const northTowns = component.getModalTowns();
      expect(northTowns.length).toBeGreaterThan(0);
      expect(northTowns.every((t) => t.district.toLowerCase().includes('north'))).toBe(true);
    });

    it('should select town from modal and close modal', () => {
      vi.spyOn(component.destinationChange, 'emit');
      vi.spyOn(component.destinationSelected, 'emit');

      component.showAllTownsModal = true;
      component.selectTownFromModal('Bongabon');

      expect(component.query).toBe('Bongabon');
      expect(component.destination).toBe('Bongabon');
      expect(component.showAllTownsModal).toBe(false);
      expect(component.destinationChange.emit).toHaveBeenCalledWith('Bongabon');
      expect(component.destinationSelected.emit).toHaveBeenCalledWith({
        destination: 'Bongabon',
        type: 'municipality',
      });
    });
  });
});
