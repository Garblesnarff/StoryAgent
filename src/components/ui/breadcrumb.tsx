import * as React from "react";
import { ChevronRight } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

const routes = {
  "/": "Home",
  "/create-story": "Create Story",
  "/upload-book": "Upload Book",
  "/story/edit": "Story Editor",
  "/story/generate": "Generate Story",
  "/story/customize": "Customize Story"
};

const Breadcrumb = () => {
  const location = useLocation();
  const pathSegments = location.pathname.split('/').filter(Boolean);
  
  const breadcrumbs = [
    { path: '/', label: 'Home' },
    ...pathSegments.map((_, index) => {
      const path = '/' + pathSegments.slice(0, index + 1).join('/');
      return {
        path,
        label: routes[path as keyof typeof routes] || pathSegments[index]
      };
    })
  ];

  return (
    <nav aria-label="Breadcrumb" className="mb-6">
      <ol className="flex items-center space-x-2 text-sm">
        {breadcrumbs.map((breadcrumb, index) => (
          <li key={breadcrumb.path} className="flex items-center">
            {index > 0 && (
              <ChevronRight className="h-4 w-4 mx-2 text-muted-foreground/50" />
            )}
            <Link
              to={breadcrumb.path}
              className={cn(
                "hover:text-primary transition-colors duration-200",
                index === breadcrumbs.length - 1
                  ? "text-primary font-semibold"
                  : "text-muted-foreground"
              )}
            >
              {breadcrumb.label}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
};

export { Breadcrumb };
