/**
 * Firebase Configuration for GCAA Analytics Dashboard
 *
 * This file initializes Firebase and exports the Firestore database instance
 * for use in the React application for real-time data sync.
 */

import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCJQ8A30DWTGpuJWDYFhR8bs2hk6lV7uCI",
  authDomain: "esg-reports-collection.firebaseapp.com",
  projectId: "esg-reports-collection",
  storageBucket: "esg-reports-collection.firebasestorage.app",
  messagingSenderId: "1814516762",
  appId: "1:1814516762:web:ba5299acda54ca1cfe2da3",
  measurementId: "G-210EF632LF"
};

let db = null;

try {
  // Initialize Firebase
  const app = initializeApp(firebaseConfig);
  // Initialize Firestore
  db = getFirestore(app);
  console.log('Firebase initialized successfully');
} catch (error) {
  console.error('Firebase initialization error:', error);
  // db remains null, will fall back to static data
}

export { db };
