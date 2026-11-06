import data from "@/content/book-themes.json";
export const bookThemes:Record<string,string>=data.themes;
export function bookTheme(id:number){return (data.assignments as Record<string,string>)[String(id)]||"research";}
