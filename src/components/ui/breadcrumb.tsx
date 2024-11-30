import { ChevronRight } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

/**
 * Interface for application route mappings
 * @interface RouteMap
 */
interface RouteMap {
  readonly [key: string]: string;
}

/**
 * Interface for breadcrumb item structure
 * @interface BreadcrumbItem
 */
interface BreadcrumbItem {
  path: string;
  label: string;
}

/**
 * Application route mappings
 * Maps URL paths to their display labels
 * 
 * @constant
 * @type {RouteMap}
 */
const routes: RouteMap = {
  "/": "Home",
  "/create-story": "Create Story",
  "/upload-book": "Upload Book",
  "/story/edit": "Story Editor",
  "/story/generate": "Generate Story",
  "/story/customize": "Customize Story"
};

/**
 * Breadcrumb Navigation Component
 * 
 * Provides hierarchical navigation path visualization using the current route.
 * Automatically generates breadcrumb items based on the current URL path.
 * 
 * Features:
 * - Dynamic path segment parsing
 * - Consistent styling with design system
 * - Accessible navigation structure
 * - Fallback handling for unknown routes
 * 
 * @component
 * @example
 * ```tsx
 * <Breadcrumb />
 * ```
 */
const Breadcrumb = () => {
  const location = useLocation();
  const pathSegments = location.pathname.split('/').filter(Boolean);
  
  const breadcrumbs: BreadcrumbItem[] = [
    { path: '/', label: 'Home' },
    ...pathSegments.map((_, index) => {
      const path = '/' + pathSegments.slice(0, index + 1).join('/');
      const label = routes[path] || pathSegments[index].replace(/-/g, ' ');
      return {
        path,
        label: label.charAt(0).toUpperCase() + label.slice(1)
      };
    })
  ];

  return (
    <nav 
      aria-label="Breadcrumb Navigation" 
      className="mb-6"
      role="navigation"
    >
      <ol 
        className="flex items-center space-x-2 text-sm"
        itemScope 
        itemType="https://schema.org/BreadcrumbList"
      >
        {breadcrumbs.map((breadcrumb, index) => (
          <li 
            key={breadcrumb.path} 
            className="flex items-center"
            itemProp="itemListElement"
            itemScope
            itemType="https://schema.org/ListItem"
          >
            {index > 0 && (
              <ChevronRight 
                className="h-4 w-4 mx-2 text-muted-foreground/50" 
                aria-hidden="true"
              />
            )}
            <Link
              to={breadcrumb.path}
              className={cn(
                "hover:text-primary transition-colors duration-200",
                "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                index === breadcrumbs.length - 1
                  ? "text-primary font-semibold aria-current-page"
                  : "text-muted-foreground"
              )}
              itemProp="item"
              aria-current={index === breadcrumbs.length - 1 ? "page" : undefined}
            >
              <span itemProp="name">{breadcrumb.label}</span>
            </Link>
            <meta itemProp="position" content={String(index + 1)} />
          </li>
        ))}
      </ol>
    </nav>
  );
};

export { Breadcrumb };
