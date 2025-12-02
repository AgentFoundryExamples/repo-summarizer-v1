// Utility functions
export function formatDate(date) {
    return date.toISOString().split('T')[0];
}

export function capitalize(str) {
    // FIXME: Handle empty strings
    return str.charAt(0).toUpperCase() + str.slice(1);
}

export const API_URL = 'https://api.example.com';
