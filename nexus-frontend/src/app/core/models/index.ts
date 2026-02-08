// =============================================================================
// RÔLES
// =============================================================================

export type UserRole = 
  | 'admin_general'
  | 'admin_chantier'
  | 'comptable'
  | 'chef_chantier'
  | 'magasinier'
  | 'ouvrier'
  | 'client'
  | 'direction';

// =============================================================================
// USER
// =============================================================================

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: UserRole;
  chantier_id?: number;
  chantiers_assignes?: number[];
  is_active: boolean;
  created_at?: string;
  last_login?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in?: number;
  user?: User;
}

export interface CreateUser {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  role: UserRole;
  chantier_id?: number;
}

export interface UpdateUser {
  first_name?: string;
  last_name?: string;
  phone?: string;
  role?: UserRole;
  chantier_id?: number;
  is_active?: boolean;
}

// =============================================================================
// CHANTIER
// =============================================================================

export type ChantierStatus = 'en_preparation' | 'planifie' | 'en_cours' | 'termine' | 'suspendu' | 'archive';

export interface Chantier {
  id: number;
  reference: string;
  nom: string;
  adresse: string;
  ville: string;
  client_nom: string;
  client_telephone?: string;
  budget_prevu: number;
  budget_consomme: number;
  progression?: number;
  date_debut?: string;
  date_fin?: string;
  date_fin_prevue?: string;
  description?: string;
  status: ChantierStatus;
  created_at: string;
  created_by?: number;
}

export interface CreateChantier {
  nom: string;
  adresse: string;
  ville?: string;
  client_nom: string;
  client_telephone?: string;
  budget_prevu: number;
  date_debut?: string;
  date_fin?: string;
  date_fin_prevue?: string;
  description?: string;
}

export interface UpdateChantier {
  nom?: string;
  adresse?: string;
  ville?: string;
  client_nom?: string;
  client_telephone?: string;
  budget_prevu?: number;
  date_debut?: string;
  date_fin?: string;
  description?: string;
  status?: ChantierStatus;
}

// =============================================================================
// DÉPENSE
// =============================================================================

export type DepenseStatus = 'en_attente' | 'validee_chantier' | 'approuvee' | 'rejetee' | 'annulee';
export type DepenseCategorie = 'materiel' | 'main_oeuvre' | 'transport' | 'location' | 'sous_traitance' | 'administratif' | 'autres';

export interface Depense {
  id: number;
  reference: string;
  chantier_id: number;
  libelle: string;
  description?: string;
  categorie: DepenseCategorie;
  montant: number;
  date_depense: string;
  fournisseur?: string;
  status: DepenseStatus;
  created_by?: number;
  approved_by?: number;
  approved_at?: string;
  rejected_by?: number;
  motif_rejet?: string;
  created_at: string;
}

export interface CreateDepense {
  chantier_id: number;
  libelle: string;
  description?: string;
  categorie: DepenseCategorie;
  montant: number;
  date_depense: string;
  fournisseur?: string;
}

export interface UpdateDepense {
  libelle?: string;
  description?: string;
  categorie?: DepenseCategorie;
  montant?: number;
  date_depense?: string;
  fournisseur?: string;
}

// =============================================================================
// EMPLOYÉ
// =============================================================================

export type PosteEmploye = 'chef_equipe' | 'macon' | 'ferrailleur' | 'electricien' | 'plombier' | 'manoeuvre' | 'conducteur' | 'gardien' | 'autres';

export interface Employe {
  id: number;
  matricule: string;
  nom: string;
  prenom: string;
  telephone?: string;
  poste: PosteEmploye;
  salaire_journalier: number;
  date_embauche: string;
  chantier_id?: number;
  is_active: boolean;
  created_at?: string;
}

export interface CreateEmploye {
  nom: string;
  prenom: string;
  telephone?: string;
  poste: PosteEmploye;
  salaire_journalier: number;
  date_embauche: string;
  chantier_id?: number;
}

export interface UpdateEmploye {
  nom?: string;
  prenom?: string;
  telephone?: string;
  poste?: PosteEmploye;
  salaire_journalier?: number;
  chantier_id?: number;
}

// =============================================================================
// POINTAGE / PRÉSENCE
// =============================================================================

export type PresenceStatus = 'present' | 'absent' | 'retard' | 'conge' | 'non_pointe';

export interface PointageEmploye {
  employe_id: number;
  nom: string;
  prenom: string;
  matricule: string;
  poste: string;
  salaire_journalier?: number;
  status: PresenceStatus;
  heures?: number;
}

export interface Presence {
  id: number;
  employe_id: number;
  chantier_id: number;
  date: string;
  status: PresenceStatus;
  heures_travaillees: number;
  created_by?: number;
  created_at?: string;
}

export interface CreatePointage {
  employe_id: number;
  chantier_id: number;
  date: string;
  status: PresenceStatus;
  heures?: number;
}

// =============================================================================
// MATÉRIEL / STOCK
// =============================================================================

export type MaterielCategorie = 'ciment' | 'fer' | 'agregat' | 'bois' | 'peinture' | 'plomberie' | 'electricite' | 'outillage' | 'autres';
export type MaterielUnite = 'sac' | 'barre' | 'm3' | 'm2' | 'ml' | 'kg' | 'piece' | 'litre' | 'rouleau';
export type TypeMouvement = 'entree' | 'sortie' | 'transfert_entrant' | 'transfert_sortant' | 'ajustement' | 'reception';

export interface Materiel {
  id: number;
  chantier_id?: number;
  nom: string;
  description?: string;
  categorie: MaterielCategorie;
  unite: MaterielUnite;
  quantite: number;
  prix_unitaire: number;
  seuil_alerte: number;
  created_at?: string;
}

export interface CreateMateriel {
  chantier_id?: number;
  nom: string;
  description?: string;
  categorie: MaterielCategorie;
  unite: MaterielUnite;
  quantite?: number;
  prix_unitaire?: number;
  seuil_alerte?: number;
}

export interface UpdateMateriel {
  nom?: string;
  description?: string;
  categorie?: MaterielCategorie;
  unite?: MaterielUnite;
  quantite?: number;
  prix_unitaire?: number;
  seuil_alerte?: number;
  chantier_id?: number;
}

export interface MouvementStock {
  id: number;
  materiel_id: number;
  type_mouvement: TypeMouvement;
  quantite: number;
  motif?: string;
  created_by?: number;
  created_at?: string;
}

export interface CreateMouvement {
  materiel_id: number;
  type_mouvement: 'entree' | 'sortie';
  quantite: number;
  motif?: string;
}

export interface TransfertRequest {
  materiel_id: number;
  quantite: number;
  chantier_source_id: number;
  chantier_destination_id: number;
  motif?: string;
}

// =============================================================================
// DOCUMENT
// =============================================================================

export type TypeDocument = 'photo' | 'video' | 'plan' | 'devis' | 'facture' | 'contrat' | 'rapport' | 'bon_livraison' | 'permis' | 'autre';

export interface Document {
  id: number;
  chantier_id: number;
  nom: string;
  type_document: TypeDocument;
  fichier_path?: string;
  taille: number;
  description?: string;
  valide_client: boolean;
  uploaded_by?: number;
  validated_client_by?: number;
  validated_client_at?: string;
  created_at: string;
}

export interface UploadDocument {
  chantier_id: number;
  type_document: TypeDocument;
  description?: string;
  file: File;
}

// =============================================================================
// NOTIFICATION
// =============================================================================

export type NotificationType = 'info' | 'warning' | 'error' | 'success';
export type NotificationCategorie = 'general' | 'stock' | 'depense' | 'tache' | 'chantier' | 'document' | 'validation' | 'paiement' | 'systeme';

export interface Notification {
  id: number;
  titre: string;
  message: string;
  type_notif: NotificationType;
  categorie?: NotificationCategorie;
  is_read: boolean;
  chantier_id?: number;
  created_at: string;
  read_at?: string;
}

// =============================================================================
// DASHBOARD
// =============================================================================

export interface DashboardStats {
  totalChantiers: number;
  chantiersEnCours: number;
  totalEmployes: number;
  employesActifs: number;
  totalDepenses: number;
  depensesEnAttente: number;
  alertesStock: number;
  budgetTotal: number;
  budgetConsomme: number;
}

export interface ChantierStats {
  id: number;
  nom: string;
  reference: string;
  status: ChantierStatus;
  budget_prevu: number;
  budget_consomme: number;
  pourcentage_budget: number;
  pourcentage_avancement: number;
  nb_employes: number;
  nb_taches_total: number;
  nb_taches_terminees: number;
}

// =============================================================================
// RAPPORTS
// =============================================================================

export interface RapportDisponible {
  id: string;
  nom: string;
  description: string;
  url: string;
  params: string[];
}

export interface SalaireEmploye {
  employe_id: number;
  matricule: string;
  nom: string;
  prenom: string;
  poste: string;
  salaire_journalier: number;
  jours_travailles: number;
  heures_totales: number;
  salaire_periode: number;
}

export interface RapportSalaires {
  chantier_id: number;
  periode: {
    debut: string;
    fin: string;
  };
  employes: SalaireEmploye[];
  total_general: number;
  nombre_employes: number;
}

// =============================================================================
// PERMISSIONS (pour le frontend)
// =============================================================================

export interface UserPermissions {
  user_id: number;
  role: UserRole;
  role_info: {
    name: string;
    color: string;
    icon: string;
    level: number;
  };
  permissions: string[];
  chantiers_assignes: number[];
}
