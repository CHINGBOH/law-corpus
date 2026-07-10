import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/graph",
      name: "graph",
      component: () => import("@/views/GraphView.vue"),
    },
    {
      path: "/review",
      name: "review",
      component: () => import("@/views/ReviewView.vue"),
    },
    {
      path: "/law",
      name: "law",
      component: () => import("@/views/ReaderView.vue"),
    },
    {
      path: "/instrument-reader",
      name: "instrument-reader",
      component: () => import("@/views/ReaderView.vue"),
    },
    {
      path: "/compare",
      name: "compare",
      component: () => import("@/views/CompareView.vue"),
    },
    {
      path: "/instrument",
      name: "instrument",
      component: () => import("@/views/InstrumentView.vue"),
    },
    {
      path: "/domain",
      name: "domain",
      component: () => import("@/views/DomainView.vue"),
    },
    {
      path: "/topic",
      name: "topic",
      component: () => import("@/views/TopicView.vue"),
    },
    {
      path: "/search",
      name: "search",
      component: () => import("@/views/SearchView.vue"),
    },
    {
      path: "/",
      name: "home",
      component: () => import("@/views/HomeView.vue"),
    },
  ],
});

export default router;
