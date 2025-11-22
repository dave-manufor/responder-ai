# Data Models - Respondr.ai

## Overview
This document defines the core data structures used in the Respondr.ai frontend, provided as TypeScript interfaces for type safety.

## Core Entities

### Hospital
Represents a hospital facility with location and capacity data.

```typescript
interface Hospital {
  _id: string;
  name: string;
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number]; // [longitude, latitude]
  };
  properties: {
    zone: string;
    icu_capacity: number;
    trauma_capacity: number;
    specialties: string[];
    contact?: string;
  };
  allocated: number;
  last_updated?: string; // ISO Date string
}
```

### Incident (Session)
Represents the current state of a mass casualty incident session.

```typescript
interface Incident {
  _id: string;
  status: "ACTIVE" | "RESOLVED" | "ARCHIVED";
  created_at: string; // ISO Date string
  location?: {
    lat: number;
    long: number;
  };
  casualty_log: CasualtyLog[];
  total_casualties: number;
  allocated_beds: number;
}
```

### Casualty Log
A record of a reported casualty or group of casualties.

```typescript
interface CasualtyLog {
  timestamp: string; // ISO Date string
  transcript: string;
  extracted_count: number;
  triage_color: "RED" | "YELLOW" | "GREEN" | "BLACK";
  primary_injury: string;
}
```

## API Request/Response Models

### Bed Reservation Request
`POST /reserve_bed`

```typescript
interface BedReservation {
  hospital_id: string;
  severity: "RED" | "YELLOW" | "GREEN" | "BLACK";
  patient_count: number;
}
```

### Allocation Request
`POST /api/allocate`

```typescript
interface AllocationRequest {
  lat: number;
  lon: number;
  patient_count: number;
  triage_color?: "RED" | "YELLOW" | "GREEN" | "BLACK"; // Default: RED
}
```

### Allocation Plan (Response)
Response from allocation endpoints.

```typescript
interface AllocationPlan {
  status: "SUCCESS" | "PARTIAL" | "OVERFLOW";
  plan: HospitalAllocation[];
  unallocated: number;
  message?: string;
}

interface HospitalAllocation {
  hospital_id: string;
  hospital_name: string;
  patients_sent: number;
  coordinates: [number, number];
  distance_km: number;
}
```

### Agent Response
Response from `POST /api/radio/text`.

```typescript
interface AgentResponse {
  session_id: string;
  transcript: string;
  action: "acknowledged" | "location_updated" | "casualty_reported" | "beds_allocated" | "triage_error" | "allocation_error";
  message: string;
  session_state?: Partial<Incident>;
  triage_result?: TriageResult;
  allocation_result?: AllocationPlan;
}

interface TriageResult {
  triage_color: "RED" | "YELLOW" | "GREEN" | "BLACK";
  primary_injury: string;
  specialty_needed: string;
  confidence: number;
  reasoning?: string;
}
```
