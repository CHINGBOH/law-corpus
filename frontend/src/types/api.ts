export interface GraphNodeRef {
  node_key: string;
  node_type?: string;
  node_type_label?: string;
  ref?: string;
  title: string;
  subtitle?: string | null;
  href?: string;
}

export interface GraphNode extends GraphNodeRef {
  hint: string;
  can_extract_candidates: boolean;
}

export interface EvidenceInfo {
  evidence_level?: string | null;
  confidence?: number | null;
  source_title?: string | null;
  source_url?: string | null;
  excerpt_text?: string | null;
}

export interface GraphNeighbor extends EvidenceInfo {
  direction: "outbound" | "inbound";
  relation_type: string;
  relation_type_label: string;
  claim_text?: string | null;
  target: GraphNodeRef;
}

export interface GraphRelationGroup {
  label: string;
  items: GraphNeighbor[];
}

export interface GraphPreset {
  label: string;
  node_key: string;
}

export interface GraphPathNode {
  node_key: string;
  title: string;
  [key: string]: unknown;
}

export interface GraphPathEdge {
  edge_key: string;
  relation_type: string;
  [key: string]: unknown;
}

export interface GraphPath {
  requested_to: string;
  nodes: GraphPathNode[];
  edges: GraphPathEdge[];
}

export interface GraphViewResponse {
  ok: boolean;
  error?: string;
  node: GraphNode;
  counts: {
    meaningful_neighbors: number;
    structural_neighbors: number;
  };
  structural_neighbors: GraphNodeRef[];
  grouped_relations: Record<string, GraphRelationGroup>;
  neighbors: GraphNeighbor[];
  presets: GraphPreset[];
  path: GraphPath | null;
}

export interface ExtractCandidatesResponse {
  ok: boolean;
  error?: string;
  created: { candidate_id: string }[];
  proposals?: number;
}

export interface CandidateSummary {
  id: string;
  relation_type: string;
  relation_type_label: string;
  subject_title?: string | null;
  object_title?: string | null;
  status: string;
  status_label: string;
  source_title?: string | null;
}

export interface CandidateDetail {
  id: string;
  status: string;
  status_label: string;
  proposer?: string | null;
  subject_title?: string | null;
  object_title?: string | null;
  claim_text?: string | null;
  relation_type: string;
  relation_type_label: string;
  confidence?: number | null;
  review_note?: string | null;
  subject_node_key: string;
  object_node_key: string;
  graph_hrefs: { subject: string; object: string; path: string };
  evidence: EvidenceInfo;
}

export interface ArticleUnit {
  version_label?: string;
  unit_number: string;
  unit_number_int: number;
  canonical_ref: string;
  text: string;
}

export interface NavGroupItem {
  unit_number: string;
  unit_number_int: number;
  href: string;
  active: boolean;
}

export interface NavGroup {
  start: number;
  end: number;
  open: boolean;
  items: NavGroupItem[];
}

export interface NavLink {
  enabled: boolean;
  href: string;
  label: string;
}

export interface SidebarLink {
  label: string;
  href: string;
}

export interface ReaderSidebar {
  meta: { label?: string; ref: string };
  actions: SidebarLink[];
  relations: SidebarLink[];
  topics: SidebarLink[];
  tip?: string;
}

export interface ReaderViewResponse {
  ok: boolean;
  error?: string;
  mode: "law" | "instrument";
  title: string;
  versions?: { slug: string; version_label: string }[];
  selected_version: string | null;
  instrument_slug?: string;
  instrument_title?: string;
  article: ArticleUnit;
  nav_groups: NavGroup[];
  prev: NavLink;
  next: NavLink;
  compare_href: string | null;
  sidebar: ReaderSidebar;
}

export interface CompareViewResponse {
  ok: boolean;
  error?: string;
  versions: { slug: string; version_label: string }[];
  left: { slug: string; article: ArticleUnit | null };
  right: { slug: string; article: ArticleUnit | null };
  article_no: number;
}

export interface ReviewBundle {
  status: string;
  status_options: string[];
  candidates: CandidateSummary[];
  selected_id: string | null;
  detail: CandidateDetail | null;
}

export interface Stats {
  instruments?: number;
  domains?: number;
  topics?: number;
  versions?: number;
  legal_relations?: number;
  relation_candidates?: number;
  plain_explanations?: number;
  [key: string]: number | undefined;
}

export interface DomainSummary {
  slug: string;
  name: string;
  description?: string | null;
  instrument_count: number;
  sort_order?: number;
}

export interface TopicSummary {
  slug: string;
  title: string;
  pillar_title?: string | null;
  question?: string | null;
  summary?: string | null;
  status?: string;
  link_count?: number;
  explanation_count?: number;
}

export interface InstrumentSummary {
  slug: string;
  short_title: string;
  canonical_title?: string | null;
  instrument_type?: string | null;
  domains?: string | null;
  current_version_label?: string | null;
  effective_date?: string | null;
  first_enacted_date?: string | null;
  source_title?: string | null;
  source_url?: string | null;
}

export interface RelationCard {
  relation_type: string;
  relation_type_label: string;
  claim_text?: string | null;
  confidence?: number | null;
  evidence_level?: string | null;
  source_title?: string | null;
  object_title?: string | null;
  href: string;
}

export interface VersionRow {
  slug: string;
  version_label: string;
  version_sequence: number;
  action_type: string;
  adopted_date?: string | null;
  effective_date?: string | null;
  status: string;
  article_count?: number;
}

export interface ContextCard {
  version_label: string;
  title: string;
  relation_type: string;
  claim_text?: string | null;
  confidence: number;
  evidence_level: string;
  source_title?: string | null;
}

export interface SourceRow {
  slug: string;
  source_type: string;
  title: string;
  url?: string | null;
  publisher?: string | null;
  reliability_tier: number;
}

export interface Pillar {
  title: string;
  question: string;
  scope: string;
  signal: string;
}

export interface HomeViewResponse {
  stats: Stats;
  domains: DomainSummary[];
  topics: TopicSummary[];
  instruments: InstrumentSummary[];
  company_relations: RelationCard[];
  versions: VersionRow[];
  contexts: ContextCard[];
  sources: SourceRow[];
  pillars: Pillar[];
}

export interface SearchResult {
  instrument_title: string;
  version_label: string;
  canonical_ref: string;
  unit_number?: string;
  title?: string;
  text?: string;
  actions: SidebarLink[];
}

export interface SearchViewResponse {
  query: string;
  results: SearchResult[];
}

export interface InstrumentDetail {
  slug: string;
  short_title: string;
  canonical_title?: string | null;
  instrument_type?: string | null;
  subject_area?: string | null;
  first_enacted_date?: string | null;
  current_version_label?: string | null;
  effective_date?: string | null;
  domains?: string | null;
  source_title?: string | null;
  source_url?: string | null;
}

export interface InstrumentUnit extends ArticleUnit {
  instrument_slug: string;
  actions: SidebarLink[];
}

export interface InstrumentViewResponse {
  ok: boolean;
  error?: string;
  instrument: InstrumentDetail;
  versions: VersionRow[];
  relations: RelationCard[];
  topics: TopicSummary[];
  units: InstrumentUnit[];
}

export interface DomainDetail {
  slug: string;
  name: string;
  description?: string | null;
  instrument_count: number;
  sort_order?: number;
}

export interface DomainInstrument extends InstrumentSummary {
  is_primary: boolean;
}

export interface DomainViewResponse {
  ok: boolean;
  error?: string;
  domain: DomainDetail;
  instruments: DomainInstrument[];
}

export interface TopicDetail {
  slug: string;
  title: string;
  pillar_title?: string | null;
  question?: string | null;
  summary?: string | null;
  status?: string;
  link_count?: number;
  explanation_count?: number;
}

export interface TopicLinkCard {
  title: string;
  href: string;
  description?: string | null;
  meta: string;
}

export interface Explanation {
  explanation_type: string;
  title: string;
  body: string;
  confidence: number;
  author?: string | null;
  source_title?: string | null;
  source_url?: string | null;
}

export interface TopicViewResponse {
  ok: boolean;
  error?: string;
  topic: TopicDetail;
  core: TopicLinkCard[];
  support: TopicLinkCard[];
  background: TopicLinkCard[];
  explanations: Explanation[];
}
