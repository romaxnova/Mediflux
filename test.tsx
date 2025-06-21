import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./frontend/src/App";
import DoctorList from "./frontend/src/components/DoctorList";

// Test rendering App
render(<App />);
console.log("Rendered App. Check for heading:");
console.log(screen.getByText(/Liste des médecins généralistes/i));

// Test rendering DoctorList directly
render(<DoctorList />);
console.log("Rendered DoctorList. Check for heading:");
console.log(screen.getByText(/Liste des médecins généralistes/i));
