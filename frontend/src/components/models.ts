export interface Todo {
  id: number;
  content: string;
}

export interface Meta {
  totalCount: number;
}

export interface Message {
  member_username: string;
  content: string
  discord_id: number;
}