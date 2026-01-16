/**
 * Firebase Configuration for GCAA Analytics Dashboard
 *
 * This file initializes Firebase and exports the Firestore database instance
 * for use in the React application for real-time data sync.
 *
 * To get your Firebase config:
 * 1. Go to https://console.firebase.google.com/
 * 2. Select project: esg-reports-collection
 * 3. Go to Project Settings (gear icon) → General tab
 * 4. Scroll down to "Your apps" → Web apps
 * 5. Copy the firebaseConfig object
 */

import { initializeApp } from 'firebase/app';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';

// Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyCJQ8A30DWTGpuJWDYFhR8bs2hk6lV7uCI",
  authDomain: "esg-reports-collection.firebaseapp.com",
  projectId: "esg-reports-collection",
  storageBucket: "esg-reports-collection.firebasestorage.app",
  messagingSenderId: "1814516762",
  appId: "1:1814516762:web:ba5299acda54ca1cfe2da3",
  measurementId: "G-210EF632LF"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore
const db = getFirestore(app);

// Optional: Connect to Firestore Emulator for local development
// Uncomment the following lines if using Firebase Emulator
// if (import.meta.env.DEV) {
//   connectFirestoreEmulator(db, 'localhost', 8080);
//   console.log('Connected to Firestore Emulator');
// }

export { db };
